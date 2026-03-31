from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.monitoring.models import AgentEvent, AgentWorkday
from apps.monitoring.services.lh_import_utils import (
    SOURCE_NAME,
    add_date_filter_arguments,
    resolve_date_window,
)


class Command(BaseCommand):
    help = "Remove importacoes do LH_ALIVE de AgentEvent e AgentWorkday em uma janela de datas."

    def add_arguments(self, parser):
        add_date_filter_arguments(parser)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Executa sem pedir confirmacao.",
        )

    def handle(self, *args, **options):
        start_date, end_date = resolve_date_window(options)
        force = options.get("force", False)
        if start_date is None and end_date is None:
            self.stdout.write("Janela de limpeza: TODOS os registros (--all)")
            workday_qs = AgentWorkday.objects.filter(source=SOURCE_NAME)
            event_qs = AgentEvent.objects.filter(source=SOURCE_NAME)
        else:
            self.stdout.write(f"Janela de limpeza: {start_date} ate {end_date}")
            event_start, event_end = self._datetime_window(start_date, end_date)
            workday_qs = AgentWorkday.objects.filter(
                source=SOURCE_NAME,
                work_date__gte=start_date,
                work_date__lte=end_date,
            )
            event_qs = AgentEvent.objects.filter(
                source=SOURCE_NAME,
                dt_inicio__gte=event_start,
                dt_inicio__lt=event_end,
            )

        workday_count = workday_qs.count()
        event_count = event_qs.count()

        self.stdout.write(f"Registros a apagar em AgentEvent: {event_count}")
        self.stdout.write(f"Registros a apagar em AgentWorkday: {workday_count}")

        if event_count == 0 and workday_count == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum registro para apagar."))
            return

        if not force:
            confirmation = input("Confirmar wipe? [y/N]: ").strip().lower()
            if confirmation not in {"y", "yes"}:
                self.stdout.write(self.style.WARNING("Operacao cancelada."))
                return

        with transaction.atomic():
            deleted_events, _ = event_qs.delete()
            deleted_workdays, _ = workday_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Resumo final: apagados AgentEvent={deleted_events}, "
                f"AgentWorkday={deleted_workdays}."
            )
        )

    @staticmethod
    def _datetime_window(start_date, end_date) -> tuple[datetime, datetime]:
        start_dt = timezone.make_aware(
            datetime.combine(start_date, time.min),
            timezone.get_current_timezone(),
        )
        end_dt = timezone.make_aware(
            datetime.combine(end_date + timedelta(days=1), time.min),
            timezone.get_current_timezone(),
        )
        return start_dt, end_dt
