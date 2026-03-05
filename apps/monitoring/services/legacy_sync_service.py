import hashlib
import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.monitoring.models import Agent, AgentDayStats, AgentEvent

logger = logging.getLogger(__name__)

EVENT_TYPES = ("LOGON", "LOGOFF", "PAUSA")
DEFAULT_LOOKBACK_MINUTES = 180


class LegacySyncService:
    def __init__(
        self,
        source_name: str = "legacy",
        lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES,
        dry_run: bool = False,
    ) -> None:
        self.source_name = source_name or "legacy"
        self.lookback_minutes = max(1, int(lookback_minutes))
        self.dry_run = dry_run

    def run(self) -> dict[str, Any]:
        window_start = timezone.now() - timedelta(minutes=self.lookback_minutes)
        logger.info(
            "Starting legacy sync: source=%s lookback=%smin dry_run=%s",
            self.source_name,
            self.lookback_minutes,
            self.dry_run,
        )

        normalized_events = self._fetch_and_normalize(window_start=window_start)
        result = {
            "agents_upserted": 0,
            "events_created": 0,
            "events_updated": 0,
            "day_stats_updated": 0,
            "window_minutes": self.lookback_minutes,
            "events_fetched": len(normalized_events),
            "sample_events": normalized_events[:3],
        }

        if self.dry_run:
            logger.info("Dry-run enabled; skipping database writes.")
            return result

        if not normalized_events:
            logger.info("No events fetched from legacy source.")
            return result

        affected_pairs: set[tuple[int, date]] = set()
        upserted_agent_ids: set[int] = set()
        events_created = 0
        events_updated = 0

        with transaction.atomic():
            for event in normalized_events:
                agent, agent_upserted = self._upsert_agent(event)
                if agent_upserted:
                    upserted_agent_ids.add(agent.id)

                created, updated = self._upsert_agent_event(event=event, agent=agent)
                events_created += created
                events_updated += updated

                affected_pairs.add((agent.id, timezone.localdate(event["dt_inicio"])))

            day_stats_updated = self._rebuild_day_stats(affected_pairs)

        result.update(
            {
                "agents_upserted": len(upserted_agent_ids),
                "events_created": events_created,
                "events_updated": events_updated,
                "day_stats_updated": day_stats_updated,
            }
        )
        logger.info("Legacy sync finished: %s", result)
        return result

    def _fetch_and_normalize(self, window_start: datetime) -> list[dict[str, Any]]:
        query = self._build_query()
        params = [*EVENT_TYPES, self._legacy_datetime(window_start)]
        raw_rows: list[dict[str, Any]] = []

        connection = self._connect_legacy()
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                raw_rows.append(dict(zip(columns, row)))
        finally:
            connection.close()

        normalized_events: list[dict[str, Any]] = []
        for row in raw_rows:
            event = self._normalize_row(row)
            if event is not None:
                normalized_events.append(event)
        return normalized_events

    def _connect_legacy(self):
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc nao esta instalado. Instale para executar sync do legado."
            ) from exc

        driver = os.getenv("LEGACY_DRIVER")
        server = os.getenv("LEGACY_SERVER")
        port = os.getenv("LEGACY_PORT")
        user = os.getenv("LEGACY_USER")
        password = os.getenv("LEGACY_PASSWORD")
        database = os.getenv("LEGACY_DATABASE")

        missing = [
            key
            for key, value in (
                ("LEGACY_DRIVER", driver),
                ("LEGACY_SERVER", server),
                ("LEGACY_USER", user),
                ("LEGACY_PASSWORD", password),
                ("LEGACY_DATABASE", database),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Variaveis de ambiente ausentes para legado: {', '.join(missing)}"
            )

        server_part = server if not port else f"{server},{port}"
        conn_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={server_part}",
            f"DATABASE={database}",
            f"UID={user}",
            f"PWD={password}",
            "TrustServerCertificate=yes",
        ]
        conn_str = ";".join(conn_parts)
        return pyodbc.connect(conn_str)

    def _build_query(self) -> str:
        schema = self._safe_identifier(os.getenv("LEGACY_SCHEMA", "dbo"), "LEGACY_SCHEMA")
        table = self._safe_identifier(
            os.getenv("LEGACY_EVENTS_TABLE", "agent_events"), "LEGACY_EVENTS_TABLE"
        )
        return f"""
            SELECT
                cd_operador,
                nm_agente,
                nm_agente_code,
                nr_ramal,
                tp_evento,
                nm_pausa,
                dt_inicio_evento,
                dt_fim_evento,
                nr_duracao_evento,
                dt_captura
            FROM [{schema}].[{table}]
            WHERE tp_evento IN (?, ?, ?)
              AND dt_captura >= ?
            ORDER BY dt_inicio_evento ASC
        """

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any] | None:
        cd_operador = self._to_positive_int(row.get("cd_operador"))
        tp_evento = self._normalize_event_type(row.get("tp_evento"))
        dt_inicio = self._to_aware_datetime(row.get("dt_inicio_evento"))
        if cd_operador is None or tp_evento is None or dt_inicio is None:
            logger.warning("Skipping invalid legacy row: %s", row)
            return None

        nm_pausa = self._to_clean_str(row.get("nm_pausa"))
        source_event_hash = self._compute_source_hash(
            source=self.source_name,
            cd_operador=cd_operador,
            tp_evento=tp_evento,
            nm_pausa=nm_pausa,
            dt_inicio=dt_inicio,
        )

        return {
            "source": self.source_name,
            "source_event_hash": source_event_hash,
            "cd_operador": cd_operador,
            "nm_agente": self._to_clean_str(row.get("nm_agente")),
            "nm_agente_code": self._to_clean_str(row.get("nm_agente_code")),
            "nr_ramal": self._to_clean_str(row.get("nr_ramal")),
            "email": self._to_clean_str(row.get("email")),
            "tp_evento": tp_evento,
            "nm_pausa": nm_pausa,
            "dt_inicio": dt_inicio,
            "dt_fim": self._to_aware_datetime(row.get("dt_fim_evento")),
            "duracao_seg": self._to_duration(row.get("nr_duracao_evento")),
            "dt_captura_origem": self._to_aware_datetime(row.get("dt_captura")),
            "raw_payload": self._json_safe(row),
        }

    def _upsert_agent(self, event: dict[str, Any]) -> tuple[Agent, bool]:
        agent, created = Agent.objects.get_or_create(
            cd_operador=event["cd_operador"],
            defaults={
                "nm_agente": event.get("nm_agente"),
                "nm_agente_code": event.get("nm_agente_code"),
                "nr_ramal": event.get("nr_ramal"),
                "email": event.get("email"),
                "ativo": True,
            },
        )
        if created:
            return agent, True

        changed_fields: list[str] = []
        for field in ("nm_agente", "nm_agente_code", "nr_ramal", "email"):
            incoming_value = event.get(field)
            if incoming_value and incoming_value != getattr(agent, field):
                setattr(agent, field, incoming_value)
                changed_fields.append(field)

        if changed_fields:
            agent.save(update_fields=changed_fields)
            return agent, True
        return agent, False

    def _upsert_agent_event(self, event: dict[str, Any], agent: Agent) -> tuple[int, int]:
        event_obj, created = AgentEvent.objects.get_or_create(
            source=event["source"],
            source_event_hash=event["source_event_hash"],
            defaults={
                "agent": agent,
                "cd_operador": event["cd_operador"],
                "tp_evento": event["tp_evento"],
                "nm_pausa": event["nm_pausa"],
                "dt_inicio": event["dt_inicio"],
                "dt_fim": event["dt_fim"],
                "duracao_seg": event["duracao_seg"],
                "dt_captura_origem": event["dt_captura_origem"],
                "raw_payload": event["raw_payload"],
            },
        )
        if created:
            return 1, 0

        changed_fields: list[str] = []

        immutable_fields = {
            "agent": agent,
            "cd_operador": event["cd_operador"],
            "tp_evento": event["tp_evento"],
            "nm_pausa": event["nm_pausa"],
            "dt_inicio": event["dt_inicio"],
        }
        for field, value in immutable_fields.items():
            if getattr(event_obj, field) != value:
                setattr(event_obj, field, value)
                changed_fields.append(field)

        for field in ("dt_fim", "duracao_seg", "dt_captura_origem"):
            value = event.get(field)
            if value is not None and getattr(event_obj, field) != value:
                setattr(event_obj, field, value)
                changed_fields.append(field)

        if (
            event.get("raw_payload") is not None
            and event_obj.raw_payload != event.get("raw_payload")
        ):
            event_obj.raw_payload = event["raw_payload"]
            changed_fields.append("raw_payload")

        if changed_fields:
            event_obj.save(update_fields=changed_fields)
            return 0, 1
        return 0, 0

    def _rebuild_day_stats(self, affected_pairs: set[tuple[int, date]]) -> int:
        if not affected_pairs:
            return 0

        current_tz = timezone.get_current_timezone()
        affected_agent_ids = {pair[0] for pair in affected_pairs}
        agents_by_id = {
            agent.id: agent for agent in Agent.objects.filter(id__in=affected_agent_ids)
        }
        updated = 0

        for agent_id, data_ref in affected_pairs:
            agent = agents_by_id.get(agent_id)
            if agent is None:
                continue

            day_start = timezone.make_aware(
                datetime.combine(data_ref, datetime.min.time()),
                current_tz,
            )
            day_end = day_start + timedelta(days=1)

            day_qs = AgentEvent.objects.filter(
                agent_id=agent_id,
                dt_inicio__gte=day_start,
                dt_inicio__lt=day_end,
            )
            aggregated = day_qs.aggregate(
                qtd_pausas=Count("id", filter=Q(tp_evento="PAUSA")),
                tempo_pausas_seg=Coalesce(Sum("duracao_seg", filter=Q(tp_evento="PAUSA")), 0),
                ultima_pausa_inicio=Max("dt_inicio", filter=Q(tp_evento="PAUSA")),
                ultima_pausa_fim=Max("dt_fim", filter=Q(tp_evento="PAUSA")),
                ultimo_logon=Max("dt_inicio", filter=Q(tp_evento="LOGON")),
                ultimo_logoff=Max("dt_inicio", filter=Q(tp_evento="LOGOFF")),
            )

            day_stats, _ = AgentDayStats.objects.get_or_create(
                agent=agent,
                data_ref=data_ref,
                defaults={"cd_operador": agent.cd_operador},
            )
            day_stats.cd_operador = agent.cd_operador
            day_stats.qtd_pausas = aggregated["qtd_pausas"] or 0
            day_stats.tempo_pausas_seg = aggregated["tempo_pausas_seg"] or 0
            day_stats.ultima_pausa_inicio = aggregated["ultima_pausa_inicio"]
            day_stats.ultima_pausa_fim = aggregated["ultima_pausa_fim"]
            day_stats.ultimo_logon = aggregated["ultimo_logon"]
            day_stats.ultimo_logoff = aggregated["ultimo_logoff"]
            day_stats.save()
            updated += 1

        return updated

    @staticmethod
    def _safe_identifier(value: str, env_key: str) -> str:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
            raise RuntimeError(f"Valor invalido para {env_key}: {value}")
        return value

    @staticmethod
    def _legacy_datetime(value: datetime) -> datetime:
        if timezone.is_aware(value):
            return timezone.make_naive(value, timezone.get_current_timezone())
        return value

    @staticmethod
    def _to_clean_str(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _to_positive_int(value: Any) -> int | None:
        try:
            integer = int(value)
        except (TypeError, ValueError):
            return None
        if integer <= 0:
            return None
        return integer

    @staticmethod
    def _to_duration(value: Any) -> int | None:
        if value is None:
            return None
        try:
            duration = int(value)
        except (TypeError, ValueError):
            return None
        if duration < 0:
            return None
        return duration

    @staticmethod
    def _normalize_event_type(value: Any) -> str | None:
        normalized = LegacySyncService._to_clean_str(value)
        if not normalized:
            return None
        normalized = normalized.upper()
        if normalized not in EVENT_TYPES:
            return None
        return normalized

    @staticmethod
    def _to_aware_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        dt_value = value
        if isinstance(value, str):
            dt_value = parse_datetime(value)
        if not isinstance(dt_value, datetime):
            return None

        if timezone.is_naive(dt_value):
            return timezone.make_aware(dt_value, timezone.get_current_timezone())
        return timezone.localtime(dt_value, timezone.get_current_timezone())

    @staticmethod
    def _compute_source_hash(
        source: str,
        cd_operador: int,
        tp_evento: str,
        nm_pausa: str | None,
        dt_inicio: datetime,
    ) -> str:
        key = "|".join(
            [
                source,
                str(cd_operador),
                tp_evento,
                nm_pausa or "",
                dt_inicio.isoformat(),
            ]
        )
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _json_safe(payload: Any) -> Any:
        def _default(value: Any):
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)

        return json.loads(json.dumps(payload, default=_default))
