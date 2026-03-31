import json
import logging
import traceback
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils import timezone

from apps.monitoring.models import JobNameChoices, JobRun, JobRunStatusChoices
from apps.monitoring.services.legacy_sync_service import (
    DEFAULT_LOOKBACK_MINUTES,
    LegacySyncService,
)
from apps.rules.models import SystemConfig, SystemConfigValueType

logger = logging.getLogger(__name__)

SYNC_CONFIG_DEFAULTS = (
    (
        "SYNC_LOOKBACK_MINUTES",
        str(DEFAULT_LOOKBACK_MINUTES),
        SystemConfigValueType.INT,
        "Janela movel do sync incremental em minutos.",
    ),
    (
        "LEGACY_SOURCE_NAME",
        "legacy",
        SystemConfigValueType.STRING,
        "Nome logico da fonte legada para dedupe de eventos.",
    ),
    (
        "LEGACY_ENABLED",
        "true",
        SystemConfigValueType.BOOL,
        "Liga/desliga o sync com a base legada.",
    ),
)


class Command(BaseCommand):
    help = "Sincroniza eventos do legado para Agent/AgentEvent e atualiza AgentDayStats."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lookback-minutes",
            type=int,
            default=None,
            help="Sobrescreve a janela de sync (em minutos).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nao grava no banco local; apenas mostra total e amostra de eventos.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        lookback_override = options["lookback_minutes"]

        config = self._load_sync_config(
            lookback_override=lookback_override,
            dry_run=dry_run,
        )

        if dry_run:
            return self._run_dry(config=config)
        return self._run_persisted(config=config)

    def _run_dry(self, config: dict[str, Any]):
        if not config["legacy_enabled"]:
            self.stdout.write(
                self.style.WARNING("LEGACY_ENABLED=false. Dry-run sem processamento.")
            )
            return

        try:
            service = LegacySyncService(
                source_name=config["legacy_source_name"],
                lookback_minutes=config["lookback_minutes"],
                dry_run=True,
            )
            stats = service.run()
        except Exception as exc:
            logger.exception("Erro durante dry-run do sync do legado.")
            raise CommandError(f"Falha no dry-run: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Dry-run concluido."))
        self.stdout.write(f"window_minutes: {stats['window_minutes']}")
        self.stdout.write(f"events_fetched: {stats['events_fetched']}")
        self.stdout.write("sample_events:")
        self.stdout.write(
            json.dumps(stats["sample_events"], indent=2, ensure_ascii=False, default=str)
        )

    def _run_persisted(self, config: dict[str, Any]):
        started_at = timezone.now()
        try:
            job_run = JobRun.objects.create(
                job_name=JobNameChoices.SYNC,
                started_at=started_at,
                status=JobRunStatusChoices.RUNNING,
            )
        except DatabaseError as exc:
            raise CommandError(
                "Falha ao iniciar JobRun. Verifique conectividade com PostgreSQL."
            ) from exc

        try:
            if not config["legacy_enabled"]:
                stats = {
                    "agents_upserted": 0,
                    "events_created": 0,
                    "events_updated": 0,
                    "day_stats_updated": 0,
                    "window_minutes": config["lookback_minutes"],
                }
                summary = "Sync ignorado: LEGACY_ENABLED=false."
            else:
                service = LegacySyncService(
                    source_name=config["legacy_source_name"],
                    lookback_minutes=config["lookback_minutes"],
                    dry_run=False,
                )
                stats = service.run()
                summary = self._build_summary(stats)

            job_run.status = JobRunStatusChoices.SUCCESS
            job_run.finished_at = timezone.now()
            job_run.summary = summary
            job_run.save(update_fields=["status", "finished_at", "summary"])

            self.stdout.write(self.style.SUCCESS("Sync concluido com sucesso."))
            self.stdout.write(summary)
        except Exception as exc:
            error_detail = traceback.format_exc()
            logger.exception("Erro durante sync do legado.")

            job_run.status = JobRunStatusChoices.ERROR
            job_run.finished_at = timezone.now()
            job_run.summary = f"Falha no sync: {exc}"
            job_run.error_detail = error_detail
            job_run.save(update_fields=["status", "finished_at", "summary", "error_detail"])
            raise CommandError("Falha ao executar sync_legacy_events.") from exc

    def _load_sync_config(self, lookback_override: int | None, dry_run: bool) -> dict[str, Any]:
        db_available = self._is_database_available()
        if db_available and not dry_run:
            self._ensure_default_configs()

        lookback_default = DEFAULT_LOOKBACK_MINUTES
        if db_available:
            lookback_default = self._get_system_config_int(
                "SYNC_LOOKBACK_MINUTES", default=DEFAULT_LOOKBACK_MINUTES
            )

        lookback_minutes = lookback_override if lookback_override is not None else lookback_default
        lookback_minutes = max(1, int(lookback_minutes))

        if db_available:
            legacy_source_name = self._get_system_config_str(
                "LEGACY_SOURCE_NAME", default="legacy"
            )
            legacy_enabled = self._get_system_config_bool("LEGACY_ENABLED", default=True)
        else:
            legacy_source_name = "legacy"
            legacy_enabled = True

        return {
            "lookback_minutes": lookback_minutes,
            "legacy_source_name": legacy_source_name,
            "legacy_enabled": legacy_enabled,
        }

    def _is_database_available(self) -> bool:
        try:
            SystemConfig.objects.exists()
            return True
        except DatabaseError:
            return False

    def _ensure_default_configs(self):
        for key, default_value, value_type, description in SYNC_CONFIG_DEFAULTS:
            SystemConfig.objects.get_or_create(
                config_key=key,
                defaults={
                    "config_value": default_value,
                    "value_type": value_type,
                    "description": description,
                },
            )

    def _get_system_config_str(self, key: str, default: str) -> str:
        config = SystemConfig.objects.filter(config_key=key).first()
        if config and config.config_value:
            return config.config_value.strip() or default
        return default

    def _get_system_config_int(self, key: str, default: int) -> int:
        config = SystemConfig.objects.filter(config_key=key).first()
        if not config:
            return default
        try:
            return int(config.config_value)
        except (TypeError, ValueError):
            return default

    def _get_system_config_bool(self, key: str, default: bool) -> bool:
        config = SystemConfig.objects.filter(config_key=key).first()
        if not config:
            return default
        return str(config.config_value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _build_summary(stats: dict[str, Any]) -> str:
        return (
            f"window_minutes={stats['window_minutes']}; "
            f"agents_upserted={stats['agents_upserted']}; "
            f"events_created={stats['events_created']}; "
            f"events_updated={stats['events_updated']}; "
            f"day_stats_updated={stats['day_stats_updated']}"
        )
