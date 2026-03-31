from django.core.management.base import BaseCommand, CommandError

from apps.monitoring.services.day_stats_service import (
    infer_rebuild_window_for_all,
    rebuild_agent_day_stats,
)
from apps.monitoring.services.lh_import_utils import add_date_filter_arguments, resolve_date_window


class Command(BaseCommand):
    help = "Recalcula AgentDayStats para uma janela de datas."

    def add_arguments(self, parser):
        add_date_filter_arguments(parser)
        parser.add_argument(
            "--source",
            type=str,
            default=None,
            help="Filtro opcional por source (ex.: LH_ALIVE).",
        )

    def handle(self, *args, **options):
        source = (options.get("source") or "").strip() or None
        start_date, end_date = resolve_date_window(options)

        if start_date is None and end_date is None:
            inferred = infer_rebuild_window_for_all(source=source)
            if inferred is None:
                self.stdout.write(self.style.WARNING("Sem dados para recalcular stats."))
                return
            start_date, end_date = inferred

        if start_date is None or end_date is None:
            raise CommandError("Falha ao resolver janela de datas para rebuild.")

        self.stdout.write(
            f"Rebuild de AgentDayStats: {start_date} ate {end_date}"
            + (f" (source={source})" if source else "")
        )
        result = rebuild_agent_day_stats(
            date_from=start_date,
            date_to=end_date,
            source=source,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Rebuild concluido: "
                f"pairs_total={result['pairs_total']}, "
                f"created={result['created']}, "
                f"updated={result['updated']}"
            )
        )
