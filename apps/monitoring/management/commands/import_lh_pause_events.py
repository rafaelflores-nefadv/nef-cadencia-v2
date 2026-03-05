import hashlib
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone
from tqdm import tqdm

from apps.monitoring.models import Agent, AgentEvent
from apps.monitoring.services.lh_import_utils import (
    SOURCE_NAME,
    add_date_filter_arguments,
    connect_legacy,
    fetch_rows,
    get_legacy_schema,
    get_row_value,
    hms_to_seconds,
    json_safe,
    resolve_date_window,
    sql_date_params,
    sql_datetime_day_range_where,
    to_aware_datetime,
    to_bigint,
    to_clean_str,
    to_positive_int,
)


class Command(BaseCommand):
    help = "Importa pausas do LH_ALIVE (VW_LH_AGENT_PAUSE_EVENTS) para AgentEvent."

    def add_arguments(self, parser):
        add_date_filter_arguments(parser)

    def handle(self, *args, **options):
        start_date, end_date = resolve_date_window(options)
        schema = get_legacy_schema(default="dbo")
        if start_date is None and end_date is None:
            self.stdout.write("Janela de importacao: TODOS os registros (--all)")
        else:
            self.stdout.write(f"Janela de importacao: {start_date} ate {end_date}")

        connection = connect_legacy()
        try:
            stats = self._import_pause_events(connection, schema, start_date, end_date)
        finally:
            connection.close()

        self.stdout.write(
            "pausas: "
            f"created={stats['created']}, "
            f"updated={stats['updated']}, "
            f"skipped={stats['skipped']}, "
            f"errors={stats['errors']}"
        )

    def _import_pause_events(
        self,
        connection,
        schema: str,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, int]:
        if start_date is None and end_date is None:
            query = f"""
                SELECT *
                FROM [{schema}].[VW_LH_AGENT_PAUSE_EVENTS]
                ORDER BY dt_event_begin ASC, ext_event ASC
            """
            params = []
        else:
            query = f"""
                SELECT
                    ext_event,
                    cd_agent,
                    name_agent,
                    status_pausa,
                    dt_event_begin,
                    dt_event_ending,
                    time_event
                FROM [{schema}].[VW_LH_AGENT_PAUSE_EVENTS]
                WHERE {sql_datetime_day_range_where('dt_event_begin')}
                ORDER BY dt_event_begin ASC, ext_event ASC
            """
            params = sql_date_params(start_date, end_date)

        rows = fetch_rows(connection=connection, query=query, params=params)
        total_rows = len(rows)
        self.stdout.write(f"Capturados {total_rows} registros (VW_LH_AGENT_PAUSE_EVENTS).")

        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        capture_time = timezone.now()

        with tqdm(
            rows,
            total=total_rows,
            desc="Importando pausas (VW_LH_AGENT_PAUSE_EVENTS)",
        ) as bar:
            for row in bar:
                ext_event_ref = get_row_value(row, "ext_event", "cd_event")
                cd_agent_ref = get_row_value(row, "cd_agent", "cd_operador")
                try:
                    ext_event = to_bigint(ext_event_ref)
                    cd_operador = to_positive_int(cd_agent_ref)
                    nm_operador = to_clean_str(
                        get_row_value(row, "name_agent", "nm_agent", "nm_agente")
                    )
                    nm_pausa = to_clean_str(get_row_value(row, "status_pausa", "nm_pausa"))
                    dt_inicio = to_aware_datetime(get_row_value(row, "dt_event_begin", "dt_inicio"))
                    dt_fim = to_aware_datetime(get_row_value(row, "dt_event_ending", "dt_fim"))
                    duracao_seg = hms_to_seconds(get_row_value(row, "time_event"))

                    if not all([ext_event, cd_operador, dt_inicio]):
                        stats["skipped"] += 1
                        continue

                    agent, created_agent = Agent.objects.get_or_create(
                        cd_operador=cd_operador,
                        defaults={
                            "nm_agente": (nm_operador or "Sem nome")[:100],
                            "ativo": True,
                        },
                    )
                    if not created_agent and nm_operador and nm_operador != agent.nm_agente:
                        agent.nm_agente = nm_operador[:100]
                        agent.save(update_fields=["nm_agente"])

                    _, created = AgentEvent.objects.update_or_create(
                        source=SOURCE_NAME,
                        ext_event=ext_event,
                        defaults={
                            "source_event_hash": self._source_event_hash(ext_event),
                            "agent": agent,
                            "cd_operador": cd_operador,
                            "tp_evento": "pause",
                            "nm_pausa": (nm_pausa or "")[:50] or None,
                            "dt_inicio": dt_inicio,
                            "dt_fim": dt_fim,
                            "duracao_seg": duracao_seg,
                            "dt_captura_origem": capture_time,
                            "raw_payload": json_safe(row),
                        },
                    )
                    if created:
                        stats["created"] += 1
                    else:
                        stats["updated"] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    self.stderr.write(
                        self.style.ERROR(
                            "[pause] erro ao processar "
                            f"ext_event={ext_event_ref} cd_agent={cd_agent_ref}: {exc}"
                        )
                    )
                finally:
                    bar.set_postfix(stats, refresh=False)

        return stats

    @staticmethod
    def _source_event_hash(ext_event: int) -> str:
        raw = f"{SOURCE_NAME}|pause|{ext_event}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
