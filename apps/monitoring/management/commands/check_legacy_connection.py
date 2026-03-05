import os
import re

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Valida conexao com SQL Server legacy (LH_ALIVE) e acesso a tabela/views."

    def handle(self, *args, **options):
        self.stdout.write("-----------------------------------")
        self.stdout.write("Validando conexao com banco legacy")
        self.stdout.write("-----------------------------------")
        self.stdout.write("")

        config = self._load_env()
        driver = config["driver"]
        server = config["server"]
        port = config["port"]
        database = config["database"]
        schema = config["schema"]

        self.stdout.write(f"Driver: {driver}")
        self.stdout.write(f"Servidor: {server}:{port}")
        self.stdout.write(f"Banco: {database}")
        self.stdout.write("")

        connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"UID={config['user']};"
            f"PWD={config['password']};"
            "TrustServerCertificate=yes;"
        )

        try:
            import pyodbc
        except ImportError as exc:
            raise CommandError(
                "pyodbc nao esta instalado. Instale para validar conexao legacy."
            ) from exc

        try:
            connection = pyodbc.connect(connection_string)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Erro ao conectar: {exc}"))
            raise CommandError("Falha ao estabelecer conexao com banco legacy.") from exc

        all_ok = True
        try:
            cursor = connection.cursor()

            if self._run_test(cursor, "SELECT 1 AS connection_ok"):
                self.stdout.write(self.style.SUCCESS("✔ Conexao estabelecida"))
            else:
                all_ok = False
                self.stdout.write(self.style.ERROR("✖ Falha no teste de conexao basica"))

            if self._run_test(cursor, f"SELECT TOP 1 * FROM {schema}.TB_EVENTOS_LH_AGENTES"):
                self.stdout.write(
                    self.style.SUCCESS("✔ Tabela TB_EVENTOS_LH_AGENTES acessivel")
                )
            else:
                all_ok = False
                self.stdout.write(
                    self.style.ERROR("✖ Nao foi possivel acessar TB_EVENTOS_LH_AGENTES")
                )

            if self._run_test(cursor, f"SELECT TOP 1 * FROM {schema}.VW_LH_AGENT_PAUSE_EVENTS"):
                self.stdout.write(
                    self.style.SUCCESS("✔ View VW_LH_AGENT_PAUSE_EVENTS acessivel")
                )
            else:
                all_ok = False
                self.stdout.write(
                    self.style.ERROR(
                        "✖ Nao foi possivel acessar VW_LH_AGENT_PAUSE_EVENTS"
                    )
                )

            if self._run_test(cursor, f"SELECT TOP 1 * FROM {schema}.VW_LH_AGENT_WORKDAY"):
                self.stdout.write(
                    self.style.SUCCESS("✔ View VW_LH_AGENT_WORKDAY acessivel")
                )
            else:
                all_ok = False
                self.stdout.write(
                    self.style.ERROR("✖ Nao foi possivel acessar VW_LH_AGENT_WORKDAY")
                )
        finally:
            connection.close()

        self.stdout.write("")
        if not all_ok:
            raise CommandError("Validacao concluida com falhas. Verifique os erros acima.")
        self.stdout.write(self.style.SUCCESS("Conexao validada com sucesso."))

    def _run_test(self, cursor, query: str) -> bool:
        try:
            cursor.execute(query)
            cursor.fetchone()
            return True
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Erro no teste '{query}': {exc}"))
            return False

    def _load_env(self) -> dict[str, str]:
        driver = os.getenv("LEGACY_DRIVER")
        server = os.getenv("LEGACY_SERVER")
        port = os.getenv("LEGACY_PORT")
        user = os.getenv("LEGACY_USER")
        password = os.getenv("LEGACY_PASSWORD")
        database = os.getenv("LEGACY_DATABASE")
        schema = os.getenv("LEGACY_SCHEMA")

        missing = [
            key
            for key, value in (
                ("LEGACY_DRIVER", driver),
                ("LEGACY_SERVER", server),
                ("LEGACY_PORT", port),
                ("LEGACY_USER", user),
                ("LEGACY_PASSWORD", password),
                ("LEGACY_DATABASE", database),
                ("LEGACY_SCHEMA", schema),
            )
            if not value
        ]
        if missing:
            raise CommandError(
                "Variaveis de ambiente ausentes: " + ", ".join(missing)
            )

        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(schema)):
            raise CommandError(f"LEGACY_SCHEMA invalido: {schema}")

        return {
            "driver": str(driver),
            "server": str(server),
            "port": str(port),
            "user": str(user),
            "password": str(password),
            "database": str(database),
            "schema": str(schema),
        }
