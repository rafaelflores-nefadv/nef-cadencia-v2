from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.monitoring.models import Agent, AgentDayStats, AgentEvent, AgentWorkday
from apps.monitoring.services.day_stats_service import rebuild_agent_day_stats

from apps.monitoring.utils import hms_to_seconds


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
    def test_dashboard_shows_data_with_fallback_when_stats_are_missing(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="dash-user", password="secret123")
        self.client.force_login(user)

        day = date(2026, 3, 5)
        tz = timezone.get_current_timezone()
        pause_start = timezone.make_aware(datetime(2026, 3, 5, 9, 0, 0), tz)
        pause_end = timezone.make_aware(datetime(2026, 3, 5, 9, 10, 0), tz)

        agent = Agent.objects.create(cd_operador=10, nm_agente="Agente Teste", ativo=True)
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="hash-dash-pause",
            ext_event=3001,
            agent=agent,
            cd_operador=10,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=pause_start,
            dt_fim=pause_end,
            duracao_seg=600,
            dt_captura_origem=pause_start,
            raw_payload={},
        )
        AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=3002,
            cd_operador=10,
            nm_operador="Agente Teste",
            work_date=day,
            dt_inicio=pause_start,
            dt_fim=timezone.make_aware(datetime(2026, 3, 5, 18, 0, 0), tz),
            duracao_seg=32400,
            dt_captura_origem=pause_start,
            raw_payload={},
        )

        response = self.client.get(reverse("dashboard"), {"data_ref": day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stats nao gerados para esta data")
        self.assertContains(response, "Total de eventos no dia")
        self.assertEqual(response.context["total_events_day"], 1)
        self.assertEqual(response.context["agents_with_activity_count"], 1)
        self.assertGreaterEqual(len(response.context["top_pause_time"]), 1)
