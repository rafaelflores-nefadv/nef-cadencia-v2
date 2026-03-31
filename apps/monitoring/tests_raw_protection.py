from datetime import date
from uuid import uuid4
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.monitoring.models import Agent, AgentEvent, AgentWorkday


class RawTableProtectionOrmTests(TestCase):
    def setUp(self):
        self.agent = Agent.objects.create(cd_operador=777001, nm_agente="Guard Test", ativo=True)
        self.now = timezone.now()

    def _create_event_record(self) -> AgentEvent:
        return AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"evt-{uuid4().hex}",
            agent=self.agent,
            cd_operador=self.agent.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=self.now,
            dt_captura_origem=self.now,
            raw_payload={},
        )

    def _create_workday_record(self) -> AgentWorkday:
        return AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=int(uuid4().int % 1_000_000_000),
            cd_operador=self.agent.cd_operador,
            nm_operador=self.agent.nm_agente,
            work_date=date(2026, 3, 5),
            dt_inicio=self.now,
            dt_fim=self.now,
            duracao_seg=0,
            dt_captura_origem=self.now,
            raw_payload={},
        )

    def test_shell_context_cannot_create_agentevent(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    self._create_event_record()

    def test_shell_context_cannot_update_or_create_agentevent(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    AgentEvent.objects.update_or_create(
                        source="LH_ALIVE",
                        source_event_hash="evt-shell-blocked-upsert",
                        defaults={
                            "agent": self.agent,
                            "cd_operador": self.agent.cd_operador,
                            "tp_evento": "PAUSA",
                            "nm_pausa": "CAFE",
                            "dt_inicio": self.now,
                            "dt_captura_origem": self.now,
                            "raw_payload": {},
                        },
                    )

    def test_shell_context_cannot_delete_agentevent(self):
        event = self._create_event_record()
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    AgentEvent.objects.filter(pk=event.pk).delete()

    def test_shell_context_cannot_create_agentworkday(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    self._create_workday_record()

    def test_shell_context_cannot_get_or_create_agentworkday(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    AgentWorkday.objects.get_or_create(
                        source="LH_ALIVE",
                        cd_operador=self.agent.cd_operador,
                        work_date=date(2026, 3, 5),
                        defaults={
                            "ext_event": int(uuid4().int % 1_000_000_000),
                            "nm_operador": self.agent.nm_agente,
                            "dt_inicio": self.now,
                            "dt_fim": self.now,
                            "duracao_seg": 0,
                            "dt_captura_origem": self.now,
                            "raw_payload": {},
                        },
                    )

    def test_shell_context_cannot_delete_agentworkday(self):
        workday = self._create_workday_record()
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    AgentWorkday.objects.filter(pk=workday.pk).delete()

    def test_shell_context_cannot_delete_using_base_manager(self):
        event = self._create_event_record()
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    AgentEvent._base_manager.filter(pk=event.pk).delete()

    def test_official_import_commands_remain_authorized(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch(
                "apps.monitoring.guards._current_manage_command",
                return_value="import_lh_pause_events",
            ):
                event, _ = AgentEvent.objects.update_or_create(
                    source="LH_ALIVE",
                    ext_event=880001,
                    defaults={
                        "source_event_hash": f"evt-{uuid4().hex}",
                        "agent": self.agent,
                        "cd_operador": self.agent.cd_operador,
                        "tp_evento": "PAUSA",
                        "nm_pausa": "CAFE",
                        "dt_inicio": self.now,
                        "dt_captura_origem": self.now,
                        "raw_payload": {},
                    },
                )
                self.assertIsNotNone(event.pk)

        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch(
                "apps.monitoring.guards._current_manage_command",
                return_value="import_lh_workday",
            ):
                workday, _ = AgentWorkday.objects.update_or_create(
                    source="LH_ALIVE",
                    cd_operador=self.agent.cd_operador,
                    work_date=date(2026, 3, 5),
                    defaults={
                        "ext_event": 880002,
                        "nm_operador": self.agent.nm_agente,
                        "dt_inicio": self.now,
                        "dt_fim": self.now,
                        "duracao_seg": 0,
                        "dt_captura_origem": self.now,
                        "raw_payload": {},
                    },
                )
                self.assertIsNotNone(workday.pk)

        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch(
                "apps.monitoring.guards._current_manage_command",
                return_value="sync_legacy_events",
            ):
                sync_event, _ = AgentEvent.objects.get_or_create(
                    source="LH_ALIVE",
                    source_event_hash=f"sync-{uuid4().hex}",
                    defaults={
                        "agent": self.agent,
                        "cd_operador": self.agent.cd_operador,
                        "tp_evento": "LOGON",
                        "dt_inicio": self.now,
                        "dt_captura_origem": self.now,
                        "raw_payload": {},
                    },
                )
                self.assertIsNotNone(sync_event.pk)

        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch(
                "apps.monitoring.guards._current_manage_command",
                return_value="wipe_lh_import",
            ):
                deleted_events, _ = AgentEvent.objects.all().delete()
                deleted_workdays, _ = AgentWorkday.objects.all().delete()
                self.assertGreaterEqual(deleted_events, 0)
                self.assertGreaterEqual(deleted_workdays, 0)


class RawTableProtectionAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_superuser(
            username="raw-admin",
            email="raw-admin@example.com",
            password="secret123",
        )
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.user
        self.agent_event_admin = admin.site._registry[AgentEvent]
        self.agent_workday_admin = admin.site._registry[AgentWorkday]

    def test_agentevent_admin_is_readonly(self):
        self.assertFalse(self.agent_event_admin.has_add_permission(self.request))
        self.assertFalse(self.agent_event_admin.has_change_permission(self.request))
        self.assertFalse(self.agent_event_admin.has_delete_permission(self.request))
        readonly = set(self.agent_event_admin.get_readonly_fields(self.request))
        model_fields = {field.name for field in AgentEvent._meta.fields}
        self.assertEqual(readonly, model_fields)

    def test_agentworkday_admin_is_readonly(self):
        self.assertFalse(self.agent_workday_admin.has_add_permission(self.request))
        self.assertFalse(self.agent_workday_admin.has_change_permission(self.request))
        self.assertFalse(self.agent_workday_admin.has_delete_permission(self.request))
        readonly = set(self.agent_workday_admin.get_readonly_fields(self.request))
        model_fields = {field.name for field in AgentWorkday._meta.fields}
        self.assertEqual(readonly, model_fields)
