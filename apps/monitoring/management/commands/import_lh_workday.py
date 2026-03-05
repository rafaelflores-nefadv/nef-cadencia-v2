from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone
from tqdm import tqdm

from apps.monitoring.models import AgentWorkday
from apps.monitoring.services.day_stats_service import rebuild_agent_day_stats
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
    sql_date_where,
    to_aware_datetime,
    to_bigint,
    to_clean_str,
    to_date,
    to_positive_int,
)


class Command(BaseCommand):
    help = "Importa jornadas do LH_ALIVE (VW_LH_AGENT_WORKDAY) para AgentWorkday."

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
            stats, affected_dates = self._import_workdays(connection, schema, start_date, end_date)
        finally:
            connection.close()

        if affected_dates:
            rebuild_result = rebuild_agent_day_stats(
                date_from=min(affected_dates),
                date_to=max(affected_dates),
                source=SOURCE_NAME,
            )
            self.stdout.write(
                "stats: "
                f"pairs_total={rebuild_result['pairs_total']}, "
                f"created={rebuild_result['created']}, "
                f"updated={rebuild_result['updated']}"
            )

        self.stdout.write(
            "jornadas: "
            f"created={stats['created']}, "
            f"updated={stats['updated']}, "
            f"skipped={stats['skipped']}, "
            f"errors={stats['errors']}"
        )

    def _import_workdays(
        self,
        connection,
        schema: str,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[dict[str, int], set[date]]:
        if start_date is None and end_date is None:
            query = f"""
                SELECT *
                FROM [{schema}].[VW_LH_AGENT_WORKDAY]
                ORDER BY work_date ASC, dt_event_begin ASC, ext_event ASC
            """
            params = []
        else:
            query = f"""
                SELECT
                    ext_event,
                    cd_agent,
                    name_agent,
                    work_date,
                    dt_event_begin,
                    dt_event_ending,
                    time_event,
                    type_event
                FROM [{schema}].[VW_LH_AGENT_WORKDAY]
                WHERE {sql_date_where('work_date')}
                ORDER BY work_date ASC, dt_event_begin ASC, ext_event ASC
            """
            params = sql_date_params(start_date, end_date)

        rows = fetch_rows(connection=connection, query=query, params=params)
        total_rows = len(rows)
        self.stdout.write(f"Capturados {total_rows} registros (VW_LH_AGENT_WORKDAY).")

        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        affected_dates: set[date] = set()
        capture_time = timezone.now()

        with tqdm(rows, total=total_rows, desc="Importando jornadas (VW_LH_AGENT_WORKDAY)") as bar:
            for row in bar:
                ext_event_ref = get_row_value(row, "ext_event", "cd_event")
                cd_agent_ref = get_row_value(row, "cd_agent", "cd_operador")
                try:
                    ext_event = to_bigint(ext_event_ref)
                    cd_operador = to_positive_int(cd_agent_ref)
                    nm_operador = to_clean_str(
                        get_row_value(row, "name_agent", "nm_agent", "nm_agente")
                    )
                    work_date = to_date(get_row_value(row, "work_date"))
                    dt_inicio = to_aware_datetime(get_row_value(row, "dt_event_begin", "dt_inicio"))
                    dt_fim = to_aware_datetime(get_row_value(row, "dt_event_ending", "dt_fim"))
                    duracao_seg = hms_to_seconds(get_row_value(row, "time_event"))

                    if not all([ext_event, cd_operador, work_date, dt_inicio, dt_fim]):
                        stats["skipped"] += 1
                        continue
                    if duracao_seg is None:
                        stats["skipped"] += 1
                        continue

                    _, created = AgentWorkday.objects.update_or_create(
                        source=SOURCE_NAME,
                        cd_operador=cd_operador,
                        work_date=work_date,
                        defaults={
                            "ext_event": ext_event,
                            "nm_operador": (nm_operador or "Sem nome")[:255],
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
                    affected_dates.add(work_date)
                except Exception as exc:
                    stats["errors"] += 1
                    self.stderr.write(
                        self.style.ERROR(
                            "[workday] erro ao processar "
                            f"ext_event={ext_event_ref} cd_agent={cd_agent_ref}: {exc}"
                        )
                    )
                finally:
                    bar.set_postfix(stats, refresh=False)

        return stats, affected_dates
