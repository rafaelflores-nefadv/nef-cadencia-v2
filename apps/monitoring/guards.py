import os
import sys

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import connection

ALLOWED_RAW_MUTATION_COMMANDS = {
    "import_lh_pause_events",
    "import_lh_workday",
    "import_lh_all",
    "import_lh_alive",
    "sync_legacy_events",
    "wipe_lh_import",
}


def assert_raw_table_mutation_allowed(model_label: str, operation: str) -> None:
    if _is_test_environment():
        return

    command = _current_manage_command()
    if command in ALLOWED_RAW_MUTATION_COMMANDS:
        return

    raise PermissionDenied(
        (
            f"{operation} bloqueado em {model_label}. "
            "As tabelas brutas de monitoring aceitam escrita apenas pelos comandos "
            "de importacao/sincronizacao oficiais."
        )
    )


def _is_test_environment() -> bool:
    db_name = str(connection.settings_dict.get("NAME") or "")
    argv = set(sys.argv)
    return any(
        (
            "PYTEST_CURRENT_TEST" in os.environ,
            db_name.startswith("test_"),
            "test" in argv,
            "pytest" in argv,
            bool(getattr(settings, "TEST", False)),
        )
    )


def _current_manage_command() -> str | None:
    if len(sys.argv) < 2:
        return None
    return sys.argv[1]
