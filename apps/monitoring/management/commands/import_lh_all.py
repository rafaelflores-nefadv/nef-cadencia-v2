from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.monitoring.services.lh_import_utils import (
    add_date_filter_arguments,
    resolve_date_window,
)


class Command(BaseCommand):
    help = "Executa import_lh_workday e import_lh_pause_events em sequencia."

    def add_arguments(self, parser):
        add_date_filter_arguments(parser)

    def handle(self, *args, **options):
        resolve_date_window(options)
        args = self._date_args(options)

        self.stdout.write("Iniciando importacao de jornadas...")
        call_command("import_lh_workday", *args)

        self.stdout.write("Iniciando importacao de pausas...")
        call_command("import_lh_pause_events", *args)

        self.stdout.write(self.style.SUCCESS("import_lh_all concluido com sucesso."))

    @staticmethod
    def _date_args(options):
        if options.get("all"):
            return ["--all"]
        if options.get("date_from") and options.get("date_to"):
            return ["--from", options["date_from"], "--to", options["date_to"]]
        if options.get("date"):
            return ["--date", options["date"]]
        if options.get("days") is not None:
            return ["--days", str(options["days"])]
        return ["--today"]
