from copy import deepcopy
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.monitoring.models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    AgentWorkday,
    JobRun,
    PauseCategoryChoices,
    PauseClassification,
)
from apps.monitoring.services.day_stats_service import rebuild_agent_day_stats
from apps.monitoring.guards import assert_raw_table_mutation_allowed

from apps.monitoring.utils import hms_to_seconds
from apps.monitoring.views import DashboardView


class HmsToSecondsTests(SimpleTestCase):
    def test_converts_hms_string(self):
        self.assertEqual(hms_to_seconds("01:02:03"), 3723)

    def test_converts_time_object(self):
        self.assertEqual(hms_to_seconds(time(2, 10, 5)), 7805)

    def test_returns_none_for_invalid_strings(self):
        self.assertIsNone(hms_to_seconds(""))
        self.assertIsNone(hms_to_seconds("10:20"))
        self.assertIsNone(hms_to_seconds("10:99:00"))
        self.assertIsNone(hms_to_seconds("abc"))


class MonitoringRawTableGuardTests(SimpleTestCase):
    def test_blocks_shell_mutation_without_override(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch("apps.monitoring.guards._current_manage_command", return_value="shell"):
                with self.assertRaises(PermissionDenied):
                    assert_raw_table_mutation_allowed("monitoring.AgentEvent", "save")

    def test_allows_import_command_mutation(self):
        with patch("apps.monitoring.guards._is_test_environment", return_value=False):
            with patch(
                "apps.monitoring.guards._current_manage_command",
                return_value="import_lh_pause_events",
            ):
                assert_raw_table_mutation_allowed("monitoring.AgentEvent", "save")


class RebuildAgentDayStatsTests(TestCase):
    def setUp(self):
        self.day = date(2026, 3, 5)
        tz = timezone.get_current_timezone()
        self.logon_dt = timezone.make_aware(datetime(2026, 3, 5, 8, 0, 0), tz)
        self.pause_start_dt = timezone.make_aware(datetime(2026, 3, 5, 10, 0, 0), tz)
        self.pause_end_dt = timezone.make_aware(datetime(2026, 3, 5, 10, 15, 0), tz)
        self.logoff_dt = timezone.make_aware(datetime(2026, 3, 5, 17, 0, 0), tz)

    def test_rebuild_creates_stats_from_events_and_workday(self):
        agent1 = Agent.objects.create(cd_operador=1, nm_agente="Agente 1", ativo=True)
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-logon",
            ext_event=1001,
            agent=agent1,
            cd_operador=1,
            tp_evento="LOGON",
            dt_inicio=self.logon_dt,
            dt_captura_origem=self.logon_dt,
            raw_payload={},
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-pause",
            ext_event=1002,
            agent=agent1,
            cd_operador=1,
            tp_evento="PAUSA",
            nm_pausa="ALMOCO",
            dt_inicio=self.pause_start_dt,
            dt_fim=self.pause_end_dt,
            duracao_seg=900,
            dt_captura_origem=self.pause_start_dt,
            raw_payload={},
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-logoff",
            ext_event=1003,
            agent=agent1,
            cd_operador=1,
            tp_evento="LOGOFF",
            dt_inicio=self.logoff_dt,
            dt_captura_origem=self.logoff_dt,
            raw_payload={},
        )
        AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=2001,
            cd_operador=2,
            nm_operador="Agente 2",
            work_date=self.day,
            dt_inicio=self.logon_dt,
            dt_fim=self.logoff_dt,
            duracao_seg=32400,
            dt_captura_origem=self.logoff_dt,
            raw_payload={},
        )

        result = rebuild_agent_day_stats(
            date_from=self.day,
            date_to=self.day,
            source="LH_ALIVE",
        )

        self.assertEqual(result["pairs_total"], 2)
        self.assertEqual(AgentDayStats.objects.filter(data_ref=self.day).count(), 2)

        stats1 = AgentDayStats.objects.get(agent__cd_operador=1, data_ref=self.day)
        self.assertEqual(stats1.qtd_pausas, 1)
        self.assertEqual(stats1.tempo_pausas_seg, 900)
        self.assertIsNotNone(stats1.ultimo_logon)
        self.assertIsNotNone(stats1.ultimo_logoff)

        stats2 = AgentDayStats.objects.get(agent__cd_operador=2, data_ref=self.day)
        self.assertEqual(stats2.qtd_pausas, 0)
        self.assertEqual(stats2.tempo_pausas_seg, 0)


class DashboardViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="dash-user", password="secret123")
        self.staff_user = user_model.objects.create_user(
            username="dash-admin",
            password="secret123",
            is_staff=True,
        )
        self.day = date(2026, 3, 5)
        self.tz = timezone.get_current_timezone()
        self.logon_dt = timezone.make_aware(datetime(2026, 3, 5, 9, 0, 0), self.tz)
        self.pause_end_dt = timezone.make_aware(datetime(2026, 3, 5, 9, 10, 0), self.tz)
        self.logoff_dt = timezone.make_aware(datetime(2026, 3, 5, 18, 0, 0), self.tz)
        self._next_ext_event = 9500000
        PauseClassification.objects.create(
            source="",
            pause_name="CAFE",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )

    def _create_base_day_data(self, include_pause=True):
        agent = Agent.objects.create(cd_operador=10, nm_agente="Agente Teste", ativo=True)
        Agent.objects.create(cd_operador=11, nm_agente="Agente Sem Atividade", ativo=True)
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-dash-logon",
            ext_event=3000,
            agent=agent,
            cd_operador=10,
            tp_evento="LOGON",
            dt_inicio=self.logon_dt,
            dt_captura_origem=self.logon_dt,
            raw_payload={},
        )
        if include_pause:
            AgentEvent.objects.create(
                source="LH_ALIVE",
                source_event_hash="hash-dash-pause",
                ext_event=3001,
                agent=agent,
                cd_operador=10,
                tp_evento="PAUSA",
                nm_pausa="CAFE",
                dt_inicio=self.logon_dt,
                dt_fim=self.pause_end_dt,
                duracao_seg=600,
                dt_captura_origem=self.logon_dt,
                raw_payload={},
            )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-dash-logoff",
            ext_event=3003,
            agent=agent,
            cd_operador=10,
            tp_evento="LOGOFF",
            dt_inicio=self.logoff_dt,
            dt_captura_origem=self.logoff_dt,
            raw_payload={},
        )
        AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=3002,
            cd_operador=10,
            nm_operador="Agente Teste",
            work_date=self.day,
            dt_inicio=self.logon_dt,
            dt_fim=self.logoff_dt,
            duracao_seg=32400,
            dt_captura_origem=self.logon_dt,
            raw_payload={},
        )
        return agent

    def _create_pause_event(self, agent, source_event_hash: str, pause_name: str, duration_seconds: int, minute_offset: int):
        start_dt = self.logon_dt + timedelta(minutes=minute_offset)
        end_dt = start_dt + timedelta(seconds=duration_seconds)
        ext_event = self._next_ext_event
        self._next_ext_event += 1
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=source_event_hash,
            ext_event=ext_event,
            agent=agent,
            cd_operador=agent.cd_operador,
            tp_evento="PAUSA",
            nm_pausa=pause_name,
            dt_inicio=start_dt,
            dt_fim=end_dt,
            duracao_seg=duration_seconds,
            dt_captura_origem=start_dt,
            raw_payload={},
        )

    def _create_operator_with_workday(self, cd_operador: int, name: str):
        agent = Agent.objects.create(cd_operador=cd_operador, nm_agente=name, ativo=True)

        logon_ext = self._next_ext_event
        self._next_ext_event += 1
        logoff_ext = self._next_ext_event
        self._next_ext_event += 1
        workday_ext = self._next_ext_event
        self._next_ext_event += 1

        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"hash-logon-{cd_operador}",
            ext_event=logon_ext,
            agent=agent,
            cd_operador=cd_operador,
            tp_evento="LOGON",
            dt_inicio=self.logon_dt,
            dt_captura_origem=self.logon_dt,
            raw_payload={},
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"hash-logoff-{cd_operador}",
            ext_event=logoff_ext,
            agent=agent,
            cd_operador=cd_operador,
            tp_evento="LOGOFF",
            dt_inicio=self.logoff_dt,
            dt_captura_origem=self.logoff_dt,
            raw_payload={},
        )
        AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=workday_ext,
            cd_operador=cd_operador,
            nm_operador=name,
            work_date=self.day,
            dt_inicio=self.logon_dt,
            dt_fim=self.logoff_dt,
            duracao_seg=32400,
            dt_captura_origem=self.logoff_dt,
            raw_payload={},
        )
        return agent

    def _create_many_operator_data(self, total_operators: int, include_pause=True):
        for index in range(total_operators):
            cd_operador = 100 + index
            agent = Agent.objects.create(
                cd_operador=cd_operador,
                nm_agente=f"Agente {cd_operador}",
                ativo=True,
            )
            logon_dt = self.logon_dt + timedelta(minutes=index)
            pause_end = logon_dt + timedelta(minutes=10)
            logoff_dt = self.logoff_dt + timedelta(minutes=index)
            AgentEvent.objects.create(
                source="LH_ALIVE",
                source_event_hash=f"hash-logon-{cd_operador}",
                ext_event=900000 + (index * 10) + 1,
                agent=agent,
                cd_operador=cd_operador,
                tp_evento="LOGON",
                dt_inicio=logon_dt,
                dt_captura_origem=logon_dt,
                raw_payload={},
            )
            if include_pause:
                AgentEvent.objects.create(
                    source="LH_ALIVE",
                    source_event_hash=f"hash-pause-{cd_operador}",
                    ext_event=900000 + (index * 10) + 2,
                    agent=agent,
                    cd_operador=cd_operador,
                    tp_evento="PAUSA",
                    nm_pausa="CAFE",
                    dt_inicio=logon_dt,
                    dt_fim=pause_end,
                    duracao_seg=600 + index,
                    dt_captura_origem=logon_dt,
                    raw_payload={},
                )
            AgentEvent.objects.create(
                source="LH_ALIVE",
                source_event_hash=f"hash-logoff-{cd_operador}",
                ext_event=900000 + (index * 10) + 3,
                agent=agent,
                cd_operador=cd_operador,
                tp_evento="LOGOFF",
                dt_inicio=logoff_dt,
                dt_captura_origem=logoff_dt,
                raw_payload={},
            )
            AgentWorkday.objects.create(
                source="LH_ALIVE",
                ext_event=800000 + index,
                cd_operador=cd_operador,
                nm_operador=f"Agente {cd_operador}",
                work_date=self.day,
                dt_inicio=logon_dt,
                dt_fim=logoff_dt,
                duracao_seg=max(0, int((logoff_dt - logon_dt).total_seconds())),
                dt_captura_origem=logon_dt,
                raw_payload={},
            )

    def _next_ext(self) -> int:
        value = self._next_ext_event
        self._next_ext_event += 1
        return value

    def _create_operator_data_for_day(
        self,
        *,
        target_day: date,
        cd_operador: int,
        pause_seconds: int = 600,
    ):
        agent, created = Agent.objects.get_or_create(
            cd_operador=cd_operador,
            defaults={"nm_agente": f"Agente {cd_operador}", "ativo": True},
        )
        if not created:
            agent.ativo = True
            if not agent.nm_agente:
                agent.nm_agente = f"Agente {cd_operador}"
            agent.save(update_fields=["ativo", "nm_agente"])

        logon_dt = timezone.make_aware(datetime.combine(target_day, time(9, 0, 0)), self.tz)
        pause_start = timezone.make_aware(datetime.combine(target_day, time(9, 20, 0)), self.tz)
        pause_end = pause_start + timedelta(seconds=pause_seconds)
        logoff_dt = timezone.make_aware(datetime.combine(target_day, time(18, 0, 0)), self.tz)

        base_hash = f"{cd_operador}-{target_day.isoformat()}"
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"logon-{base_hash}",
            ext_event=self._next_ext(),
            agent=agent,
            cd_operador=cd_operador,
            tp_evento="LOGON",
            dt_inicio=logon_dt,
            dt_captura_origem=logon_dt,
            raw_payload={},
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"pause-{base_hash}",
            ext_event=self._next_ext(),
            agent=agent,
            cd_operador=cd_operador,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=pause_start,
            dt_fim=pause_end,
            duracao_seg=pause_seconds,
            dt_captura_origem=pause_start,
            raw_payload={},
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=f"logoff-{base_hash}",
            ext_event=self._next_ext(),
            agent=agent,
            cd_operador=cd_operador,
            tp_evento="LOGOFF",
            dt_inicio=logoff_dt,
            dt_captura_origem=logoff_dt,
            raw_payload={},
        )
        AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=self._next_ext(),
            cd_operador=cd_operador,
            nm_operador=agent.nm_agente,
            work_date=target_day,
            dt_inicio=logon_dt,
            dt_fim=logoff_dt,
            duracao_seg=int((logoff_dt - logon_dt).total_seconds()),
            dt_captura_origem=logoff_dt,
            raw_payload={},
        )
        return agent

    def test_rankings_show_10_when_more_than_10_operators(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=12, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["top_pause_time"]), 10)
        self.assertEqual(len(response.context["top_pause_count"]), 10)
        self.assertEqual(len(response.context["top_productivity"]), 10)
        self.assertContains(response, "Maiores pausas por tipo")
        self.assertContains(response, "Top agentes")

    def test_risk_block_shows_10_when_more_than_10_operators(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=12, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["risk_agents"]), 10)
        self.assertContains(response, "Radar de criticidade")
        self.assertEqual(len(response.context["executive_pause_radar"]), 5)

    def test_risk_block_shows_3_when_three_operators(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=3, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["risk_agents"]), 3)
        self.assertContains(response, "Radar de criticidade")
        self.assertEqual(len(response.context["executive_pause_radar"]), 5)

    def test_risk_block_shows_1_when_one_operator(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=1, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["risk_agents"]), 1)
        self.assertContains(response, "Radar de criticidade")
        self.assertEqual(len(response.context["executive_pause_radar"]), 5)

    def test_agent_with_high_harmful_time_ranks_higher_in_risk(self):
        self.client.force_login(self.user)
        agent_high = self._create_operator_with_workday(301, "Alto Improdutivo")
        agent_low = self._create_operator_with_workday(302, "Baixo Improdutivo")

        self._create_pause_event(agent_high, "hash-harmful-high", "CAFE", 3 * 3600, 5)
        self._create_pause_event(agent_low, "hash-harmful-low", "CAFE", 10 * 60, 8)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        risk_agents = response.context["risk_agents"]
        self.assertGreaterEqual(len(risk_agents), 2)
        self.assertEqual(risk_agents[0]["cd_operador"], 301)
        self.assertIn("improdutivo", risk_agents[0]["primary_reason"])
        self.assertNotEqual(risk_agents[0]["primary_reason"], "sem atividade")
        self.assertNotEqual(risk_agents[0]["tempo_improdutivo_hhmm"], "00:00:00")

    def test_high_productive_time_is_not_unduly_penalized(self):
        self.client.force_login(self.user)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        agent_productive = self._create_operator_with_workday(311, "Produtivo")
        agent_harmful = self._create_operator_with_workday(312, "Improdutivo")

        self._create_pause_event(agent_productive, "hash-legal-high", "ATENDIMENTO", 8 * 3600, 10)
        self._create_pause_event(agent_harmful, "hash-harmful-mid", "CAFE", 2 * 3600, 12)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(311, risk_by_cd)
        self.assertIn(312, risk_by_cd)
        self.assertLess(risk_by_cd[311]["risk_score"], risk_by_cd[312]["risk_score"])
        self.assertNotIn("improdutivo", risk_by_cd[311]["primary_reason"])
        self.assertGreater(risk_by_cd[311]["taxa_ocupacao_pct"], 0)

    def test_low_occupancy_adds_risk_penalty(self):
        self.client.force_login(self.user)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        agent_low_occ = self._create_operator_with_workday(321, "Baixa Ocupacao")
        agent_good_occ = self._create_operator_with_workday(322, "Boa Ocupacao")

        self._create_pause_event(agent_low_occ, "hash-legal-low", "ATENDIMENTO", 20 * 60, 14)
        self._create_pause_event(agent_good_occ, "hash-legal-high", "ATENDIMENTO", 7 * 3600, 16)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(321, risk_by_cd)
        self.assertIn(322, risk_by_cd)
        self.assertGreater(risk_by_cd[321]["risk_score"], risk_by_cd[322]["risk_score"])
        self.assertIn("ocupacao", risk_by_cd[321]["primary_reason"])

    def test_logged_agent_without_pause_uses_workday_fallback_for_productivity(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)
        self._create_operator_with_workday(410, "Logado Sem Atividade")

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        operator_metrics = {
            item["cd_operador"]: item for item in response.context["operator_metrics"]
        }
        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(410, operator_metrics)
        self.assertEqual(operator_metrics[410]["tempo_produtivo_hhmm"], "09:00:00")
        self.assertEqual(operator_metrics[410]["taxa_ocupacao_pct"], 100.0)
        self.assertEqual(operator_metrics[410]["productivity_basis"], "logged_time_fallback")
        self.assertEqual(operator_metrics[410]["logged_source"], "workday")
        self.assertIn(410, risk_by_cd)
        self.assertNotEqual(risk_by_cd[410]["primary_reason"], "sem atividade")

    def test_agent_with_relevant_events_is_not_flagged_as_no_activity(self):
        self.client.force_login(self.user)
        agent = self._create_operator_with_workday(420, "Com Pausas")
        self._create_pause_event(agent, "hash-harmful-420", "CAFE", 15 * 60, 7)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(420, risk_by_cd)
        self.assertNotEqual(risk_by_cd[420]["primary_reason"], "sem atividade")

    def test_active_agent_without_logon_or_events_is_not_marked_as_no_activity_in_risk(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertNotIn(11, risk_by_cd)
        no_activity_ids = [item["cd_operador"] for item in response.context["no_activity_agents"]]
        self.assertIn(11, no_activity_ids)

    def test_unclassified_pauses_generate_light_alert(self):
        self.client.force_login(self.user)
        agent = self._create_operator_with_workday(330, "Nao Classificado")
        self._create_pause_event(agent, "hash-unclassified-a", "PAUSA-X", 20 * 60, 9)
        self._create_pause_event(agent, "hash-unclassified-b", "PAUSA-Y", 25 * 60, 18)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        alerts = [
            alert
            for alert in response.context["alerts"]
            if "nao classific" in alert["title"].lower()
        ]
        self.assertTrue(alerts)
        self.assertTrue(all(alert["severity"] in {"info", "warn"} for alert in alerts))

    def test_rankings_show_3_when_three_operators(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=3, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["top_pause_time"]), 3)
        self.assertEqual(len(response.context["top_pause_count"]), 3)
        self.assertEqual(len(response.context["top_productivity"]), 3)
        self.assertContains(response, "Top agentes")

    def test_rankings_show_1_when_one_operator(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=1, include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["top_pause_time"]), 1)
        self.assertEqual(len(response.context["top_pause_count"]), 1)
        self.assertEqual(len(response.context["top_productivity"]), 1)
        self.assertContains(response, "Top agentes")

    def test_dashboard_with_stats_populates_summary_and_rankings(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)
        rebuild_agent_day_stats(date_from=self.day, date_to=self.day, source="LH_ALIVE")

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saude operacional do turno")
        self.assertGreaterEqual(response.context["agents_with_stats_count"], 1)
        self.assertGreaterEqual(len(response.context["top_productivity"]), 1)
        self.assertGreaterEqual(len(response.context["alerts"]), 1)

    def test_dashboard_fallback_without_stats(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["stats_warning"])
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["agents_with_activity_count"], 1)
        self.assertEqual(response.context["media_pausas_por_agente"], 1.0)
        self.assertGreaterEqual(len(response.context["top_productivity"]), 1)
        self.assertEqual(response.context["pause_data_state"], "present")

    def test_dashboard_filters_by_year(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2025, 12, 31), cd_operador=701)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=702)

        response = self.client.get(reverse("dashboard"), {"year": "2026"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["workday_count"], 1)
        self.assertEqual(response.context["selected_year"], 2026)
        self.assertEqual(response.context["selected_month"], None)
        self.assertEqual(response.context["applied_period_label"], "01/01/2026 ate 31/12/2026")

    def test_dashboard_filters_by_year_and_month(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=711)
        self._create_operator_data_for_day(target_day=date(2026, 4, 2), cd_operador=712)

        response = self.client.get(reverse("dashboard"), {"year": "2026", "month": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["workday_count"], 1)
        self.assertEqual(response.context["selected_year"], 2026)
        self.assertEqual(response.context["selected_month"], 3)
        self.assertEqual(response.context["applied_period_label"], "01/03/2026 ate 31/03/2026")

    def test_dashboard_filters_by_custom_date_range(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=721)
        self._create_operator_data_for_day(target_day=date(2026, 3, 6), cd_operador=722)
        self._create_operator_data_for_day(target_day=date(2026, 3, 8), cd_operador=723)

        response = self.client.get(
            reverse("dashboard"),
            {"date_from": "2026-03-05", "date_to": "2026-03-06"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 6)
        self.assertEqual(response.context["workday_count"], 2)
        self.assertEqual(response.context["selected_date_from"], date(2026, 3, 5))
        self.assertEqual(response.context["selected_date_to"], date(2026, 3, 6))
        self.assertEqual(response.context["applied_period_label"], "05/03/2026 ate 06/03/2026")

    def test_dashboard_rejects_invalid_custom_date_range(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=731)
        self._create_operator_data_for_day(target_day=date(2026, 3, 6), cd_operador=732)

        response = self.client.get(
            reverse("dashboard"),
            {
                "date_from": "2026-03-06",
                "date_to": "2026-03-05",
                "data_ref": "2026-03-05",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["filter_warning"], "Data inicial não pode ser maior que data final.")
        self.assertEqual(response.context["applied_period_label"], "05/03/2026")

    def test_dashboard_requires_year_when_filtering_by_month_only(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=741)

        response = self.client.get(
            reverse("dashboard"),
            {"month": "3", "data_ref": "2026-03-05"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["filter_warning"], "Filtro por mês exige ano.")
        self.assertEqual(response.context["applied_period_label"], "05/03/2026")

    def test_dashboard_quick_range_filters_this_month(self):
        self.client.force_login(self.user)
        self._create_operator_data_for_day(target_day=date(2026, 3, 5), cd_operador=751)
        self._create_operator_data_for_day(target_day=date(2026, 2, 28), cd_operador=752)

        with patch(
            "apps.monitoring.services.dashboard_period_filter.timezone.localdate",
            return_value=date(2026, 3, 6),
        ):
            response = self.client.get(reverse("dashboard"), {"quick_range": "this_month"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_events_day"], 3)
        self.assertEqual(response.context["selected_quick_range"], "this_month")
        self.assertEqual(response.context["selected_date_from"], date(2026, 3, 1))
        self.assertEqual(response.context["selected_date_to"], date(2026, 3, 6))

    def test_productivity_ranking_only_shows_agents_with_positive_productive_time(self):
        self.client.force_login(self.user)
        agent = self._create_base_day_data(include_pause=False)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        self._create_pause_event(agent, "hash-legal-prod", "ATENDIMENTO", 45 * 60, 12)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        top_productivity = response.context["top_productivity"]
        self.assertEqual(len(top_productivity), 1)
        self.assertEqual(top_productivity[0]["cd_operador"], 10)
        self.assertGreater(top_productivity[0]["tempo_produtivo_seg"], 0)
        self.assertNotEqual(top_productivity[0]["tempo_produtivo_hhmm"], "00:00:00")

    def test_harmful_pause_agent_appears_in_harmful_ranking_and_not_as_no_activity(self):
        self.client.force_login(self.user)
        agent = self._create_operator_with_workday(515, "Operador Harmful")
        self._create_pause_event(agent, "hash-harmful-515", "CAFE", 40 * 60, 11)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        top_pause_time_ids = [item["cd_operador"] for item in response.context["top_pause_time"]]
        self.assertIn(515, top_pause_time_ids)

        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(515, risk_by_cd)
        self.assertNotEqual(risk_by_cd[515]["primary_reason"], "sem atividade")
        self.assertGreater(risk_by_cd[515]["score"], 0)

    def test_dashboard_refresh_keeps_consistent_rankings_and_risk(self):
        self.client.force_login(self.user)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        productive_agent = self._create_operator_with_workday(610, "Produtivo Estavel")
        harmful_agent = self._create_operator_with_workday(611, "Improdutivo Estavel")
        self._create_pause_event(productive_agent, "hash-legal-610", "ATENDIMENTO", 50 * 60, 10)
        self._create_pause_event(harmful_agent, "hash-harmful-611", "CAFE", 35 * 60, 15)

        url = reverse("dashboard")
        params = {"data_ref": self.day.isoformat()}
        response_a = self.client.get(url, params)
        response_b = self.client.get(url, params)
        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(response_b.status_code, 200)

        rank_a = [(item["cd_operador"], item["tempo_pausas_seg"]) for item in response_a.context["top_pause_time"]]
        rank_b = [(item["cd_operador"], item["tempo_pausas_seg"]) for item in response_b.context["top_pause_time"]]
        self.assertEqual(rank_a, rank_b)

        risk_a = [
            (item["cd_operador"], item["risk_score"], item["primary_reason"])
            for item in response_a.context["risk_agents"]
        ]
        risk_b = [
            (item["cd_operador"], item["risk_score"], item["primary_reason"])
            for item in response_b.context["risk_agents"]
        ]
        self.assertEqual(risk_a, risk_b)

    def test_risk_builder_does_not_mutate_operator_metrics(self):
        operator_metrics = [
            {
                "cd_operador": 9001,
                "agent_name": "Operador Imutavel",
                "qtd_improdutivas": 2,
                "tempo_improdutivo_seg": 900,
                "tempo_neutro_seg": 0,
                "tempo_nao_classificado_seg": 0,
                "tempo_produtivo_seg": 300,
                "tempo_logado_seg": 3600,
                "taxa_ocupacao_pct": 8.33,
                "qtd_eventos_relevantes": 3,
            }
        ]
        original_metrics = deepcopy(operator_metrics)

        risk_agents = DashboardView._build_risk_agents(
            operator_metrics=operator_metrics,
            risk_config=DashboardView.RISK_CONFIG,
        )

        self.assertEqual(operator_metrics, original_metrics)
        self.assertEqual(len(risk_agents), 1)
        self.assertEqual(risk_agents[0]["cd_operador"], 9001)
        self.assertIn("score", risk_agents[0])

    def test_risk_generation_does_not_empty_productivity_ranking(self):
        self.client.force_login(self.user)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        productive_agent = self._create_operator_with_workday(920, "Produtivo Com Risco")
        harmful_agent = self._create_operator_with_workday(921, "Improdutivo Com Risco")
        self._create_pause_event(productive_agent, "hash-prod-920", "ATENDIMENTO", 40 * 60, 9)
        self._create_pause_event(harmful_agent, "hash-harm-921", "CAFE", 30 * 60, 11)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        top_productivity_ids = [item["cd_operador"] for item in response.context["top_productivity"]]
        self.assertIn(920, top_productivity_ids)
        self.assertTrue(response.context["risk_agents"])

    def test_risk_generation_does_not_remove_agents_from_harmful_rankings(self):
        self.client.force_login(self.user)
        harmful_a = self._create_operator_with_workday(930, "Harmful A")
        harmful_b = self._create_operator_with_workday(931, "Harmful B")
        self._create_pause_event(harmful_a, "hash-harm-930", "CAFE", 25 * 60, 10)
        self._create_pause_event(harmful_b, "hash-harm-931", "CAFE", 20 * 60, 15)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        top_pause_time_ids = [item["cd_operador"] for item in response.context["top_pause_time"]]
        top_pause_count_ids = [item["cd_operador"] for item in response.context["top_pause_count"]]
        self.assertIn(930, top_pause_time_ids)
        self.assertIn(931, top_pause_time_ids)
        self.assertIn(930, top_pause_count_ids)
        self.assertIn(931, top_pause_count_ids)

    def test_stats_fallback_restores_activity_and_productivity_when_events_are_sparse(self):
        self.client.force_login(self.user)
        agent = Agent.objects.create(cd_operador=950, nm_agente="Stats Fallback", ativo=True)
        AgentDayStats.objects.create(
            agent=agent,
            cd_operador=950,
            data_ref=self.day,
            qtd_pausas=1,
            tempo_pausas_seg=1800,
            ultima_pausa_inicio=self.logon_dt + timedelta(hours=1),
            ultima_pausa_fim=self.logon_dt + timedelta(hours=1, minutes=30),
            ultimo_logon=self.logon_dt,
            ultimo_logoff=self.logoff_dt,
        )

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context["agents_with_activity_count"], 1)
        self.assertEqual(response.context["tempo_produtivo_total_hhmm"], "08:30:00")

        top_productivity_ids = [item["cd_operador"] for item in response.context["top_productivity"]]
        self.assertIn(950, top_productivity_ids)

    def test_stats_count_uses_only_rows_with_activity_signal(self):
        self.client.force_login(self.user)
        agent_signal = Agent.objects.create(cd_operador=960, nm_agente="Stats Com Sinal", ativo=True)
        agent_empty_a = Agent.objects.create(cd_operador=961, nm_agente="Stats Vazio A", ativo=True)
        agent_empty_b = Agent.objects.create(cd_operador=962, nm_agente="Stats Vazio B", ativo=True)

        AgentDayStats.objects.create(
            agent=agent_signal,
            cd_operador=960,
            data_ref=self.day,
            qtd_pausas=0,
            tempo_pausas_seg=0,
            ultimo_logon=self.logon_dt,
            ultimo_logoff=self.logoff_dt,
        )
        AgentDayStats.objects.create(
            agent=agent_empty_a,
            cd_operador=961,
            data_ref=self.day,
            qtd_pausas=0,
            tempo_pausas_seg=0,
        )
        AgentDayStats.objects.create(
            agent=agent_empty_b,
            cd_operador=962,
            data_ref=self.day,
            qtd_pausas=0,
            tempo_pausas_seg=0,
        )

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["agents_with_stats_total_count"], 3)
        self.assertEqual(response.context["agents_with_stats_count"], 1)
        self.assertEqual(response.context["agents_with_activity_count"], 1)
        stats_panel = next(
            item for item in response.context["completeness_panel"] if item["key"] == "stats"
        )
        self.assertEqual(stats_panel["count"], 1)
        self.assertIn("Registros totais: 3", stats_panel["hint"])

    def test_ranking_title_counts_match_rendered_rows(self):
        self.client.force_login(self.user)
        self._create_many_operator_data(total_operators=6, include_pause=True)
        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        top_pause_time_len = len(response.context["top_pause_time"])
        top_pause_count_len = len(response.context["top_pause_count"])
        top_productivity_len = len(response.context["top_productivity"])

        self.assertEqual(top_pause_time_len, 6)
        self.assertEqual(top_pause_count_len, 6)
        self.assertEqual(top_productivity_len, 6)
        self.assertContains(response, "Top agentes")

    def test_dashboard_without_pause_dataset_shows_hint_and_na(self):
        self.client.force_login(self.user)
        Agent.objects.create(cd_operador=77, nm_agente="Sem dados", ativo=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pause_data_state"], "missing")
        self.assertEqual(response.context["total_pausas_display"], "N/A")
        self.assertIn("Sem dados de pausas importados", response.context["pause_block_message"])
        self.assertIn("python manage.py import_lh_pause_events --date 2026-03-05", response.context["pause_block_message"])

    def test_dashboard_aggregates_pause_times_by_classification(self):
        self.client.force_login(self.user)
        agent = self._create_base_day_data(include_pause=False)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        PauseClassification.objects.create(
            source="",
            pause_name="TREINAMENTO",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )

        self._create_pause_event(agent, "hash-pause-legal", "ATENDIMENTO", 600, 10)
        self._create_pause_event(agent, "hash-pause-neutral", "TREINAMENTO", 300, 25)
        self._create_pause_event(agent, "hash-pause-harmful", "CAFE", 900, 40)
        self._create_pause_event(agent, "hash-pause-unclassified", "PAUSA X", 120, 55)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        totals = response.context["pause_classification_totals_seg"]
        self.assertEqual(totals[PauseCategoryChoices.LEGAL], 600)
        self.assertEqual(totals[PauseCategoryChoices.NEUTRAL], 300)
        self.assertEqual(totals[PauseCategoryChoices.HARMFUL], 900)
        self.assertEqual(totals["UNCLASSIFIED"], 120)
        self.assertEqual(response.context["tempo_produtivo_total_hhmm"], "00:10:00")
        self.assertEqual(response.context["tempo_improdutivo_total_hhmm"], "00:15:00")
        self.assertEqual(response.context["tempo_nao_classificado_total_hhmm"], "00:02:00")

        expected_occupancy = round((600 / 32400) * 100, 2)
        self.assertEqual(response.context["taxa_ocupacao_pct"], expected_occupancy)

    def test_dashboard_counts_source_specific_legal_classification_as_productive(self):
        self.client.force_login(self.user)
        agent = self._create_base_day_data(include_pause=False)
        PauseClassification.objects.create(
            source="LH_ALIVE",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )

        self._create_pause_event(agent, "hash-source-legal", "ATENDIMENTO", 3600, 20)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        totals = response.context["pause_classification_totals_seg"]
        self.assertEqual(totals[PauseCategoryChoices.LEGAL], 3600)
        self.assertEqual(response.context["tempo_produtivo_total_hhmm"], "01:00:00")
        self.assertEqual(response.context["tempo_improdutivo_total_hhmm"], "00:00:00")
        self.assertEqual(response.context["tempo_neutro_total_hhmm"], "00:00:00")

        expected_occupancy = round((3600 / 32400) * 100, 2)
        self.assertEqual(response.context["taxa_ocupacao_pct"], expected_occupancy)

        top_productivity = response.context["top_productivity"]
        self.assertTrue(top_productivity)
        self.assertEqual(top_productivity[0]["cd_operador"], 10)
        self.assertEqual(top_productivity[0]["tempo_produtivo_hhmm"], "01:00:00")

    def test_logged_agent_with_only_harmful_pause_uses_operational_productivity_fallback(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tempo_produtivo_total_hhmm"], "08:50:00")
        self.assertEqual(response.context["tempo_improdutivo_total_hhmm"], "00:10:00")
        expected_occupancy = round((31800 / 32400) * 100, 2)
        self.assertEqual(response.context["taxa_ocupacao_pct"], expected_occupancy)

        risk_by_cd = {item["cd_operador"]: item for item in response.context["risk_agents"]}
        self.assertIn(10, risk_by_cd)
        self.assertEqual(risk_by_cd[10]["taxa_ocupacao_pct"], expected_occupancy)

    def test_dashboard_shows_distribution_and_alert_for_unclassified_pauses(self):
        self.client.force_login(self.user)
        agent = self._create_base_day_data(include_pause=False)
        self._create_pause_event(agent, "hash-pause-unclassified-1", "SEM MAPEAMENTO", 180, 15)
        self._create_pause_event(agent, "hash-pause-harmful-1", "CAFE", 240, 35)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        distribution = response.context["pause_distribution"]
        labels = {item["pause_type"] for item in distribution}
        self.assertIn("Tempo Improdutivo", labels)
        self.assertIn("Tempo Não Classificado", labels)

        top_pause_time = response.context["top_pause_time"]
        self.assertTrue(top_pause_time)
        self.assertEqual(top_pause_time[0]["tempo_pausas_hhmm"], "00:04:00")

        alerts = response.context["alerts"]
        self.assertTrue(any("nao classificadas" in alert["title"].lower() for alert in alerts))

    def test_dashboard_populates_executive_chart_series_from_database(self):
        self.client.force_login(self.user)
        agent = self._create_base_day_data(include_pause=False)
        PauseClassification.objects.create(
            source="",
            pause_name="ATENDIMENTO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )

        self._create_pause_event(agent, "hash-pause-legal-chart", "ATENDIMENTO", 600, 20)
        self._create_pause_event(agent, "hash-pause-harmful-chart", "CAFE", 900, 40)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        pause_type_by_time = response.context["pause_type_by_time"]
        self.assertTrue(pause_type_by_time)
        self.assertEqual(pause_type_by_time[0]["label"], "CAFE")
        self.assertEqual(pause_type_by_time[0]["tempo_hhmm"], "00:15:00")

        executive_timeline = response.context["executive_timeline"]
        self.assertEqual(len(executive_timeline), 24)
        self.assertGreater(sum(item["event_count"] for item in executive_timeline), 0)
        self.assertGreater(sum(item["critical_count"] for item in executive_timeline), 0)

        radar_labels = [item["label"] for item in response.context["executive_pause_radar"]]
        self.assertEqual(
            radar_labels,
            [
                "Tempo improdutivo",
                "Qtd improdutivas",
                "Baixa ocupacao",
                "Nao classificado",
                "Sem atividade",
            ],
        )

    def test_dashboard_productivity_builds_daily_evolution_from_database(self):
        self.client.force_login(self.user)
        first_day = date(2026, 3, 5)
        second_day = date(2026, 3, 6)
        self._create_operator_data_for_day(target_day=first_day, cd_operador=701, pause_seconds=600)
        self._create_operator_data_for_day(target_day=second_day, cd_operador=702, pause_seconds=1800)

        response = self.client.get(
            reverse("dashboard-productivity"),
            {"date_from": first_day.isoformat(), "date_to": second_day.isoformat()},
        )
        self.assertEqual(response.status_code, 200)

        evolution = response.context["productivity_evolution"]
        self.assertEqual([item["date_iso"] for item in evolution], [first_day.isoformat(), second_day.isoformat()])
        self.assertEqual(evolution[0]["improductive_seconds"], 600)
        self.assertEqual(evolution[1]["improductive_seconds"], 1800)
        self.assertEqual(evolution[0]["productive_hhmm"], "08:50:00")
        self.assertEqual(evolution[1]["productive_hhmm"], "08:30:00")
        self.assertGreater(evolution[0]["occupancy_pct"], evolution[1]["occupancy_pct"])

    def test_dashboard_risk_uses_active_agents_without_any_activity(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=True)

        response = self.client.get(reverse("dashboard-risk"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)

        no_activity_ids = [item["cd_operador"] for item in response.context["no_activity_agents"]]
        self.assertIn(11, no_activity_ids)
        risk_radar = {item["label"]: item["value"] for item in response.context["risk_radar_dimensions"]}
        self.assertGreater(risk_radar["Sem atividade"], 0)

    def test_completeness_panel_detects_presence_and_absence(self):
        self.client.force_login(self.user)
        self._create_base_day_data(include_pause=False)

        response = self.client.get(reverse("dashboard"), {"data_ref": self.day.isoformat()})
        self.assertEqual(response.status_code, 200)
        panel = {item["key"]: item for item in response.context["completeness_panel"]}
        self.assertEqual(panel["events"]["status"], "OK")
        self.assertEqual(panel["workday"]["status"], "OK")
        self.assertEqual(panel["stats"]["status"], "EMPTY")
        self.assertEqual(panel["pauses"]["status"], "EMPTY")

    def test_rebuild_stats_endpoint_creates_stats_and_jobrun(self):
        self.client.force_login(self.staff_user)
        self._create_base_day_data(include_pause=True)

        response = self.client.post(
            reverse("dashboard-rebuild-day-stats"),
            {"data_ref": self.day.isoformat()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AgentDayStats.objects.filter(data_ref=self.day).exists())
        run = JobRun.objects.order_by("-started_at").first()
        self.assertIsNotNone(run)
        self.assertEqual(run.status, "SUCCESS")
