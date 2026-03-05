from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.assistant.services.tools_read import (
    get_current_pauses,
    get_day_summary,
    get_pause_ranking,
)
from apps.monitoring.models import Agent, AgentDayStats, AgentEvent
from apps.rules.models import SystemConfig, SystemConfigValueType


class ToolsReadTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.now = timezone.now()

        self.agent_1 = Agent.objects.create(cd_operador=1001, nm_agente="Alice")
        self.agent_2 = Agent.objects.create(cd_operador=1002, nm_agente="Bruno")
        self.agent_3 = Agent.objects.create(cd_operador=1003, nm_agente="Carla")

        AgentDayStats.objects.create(
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            data_ref=self.today,
            qtd_pausas=4,
            tempo_pausas_seg=45 * 60,
        )
        AgentDayStats.objects.create(
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            data_ref=self.today,
            qtd_pausas=2,
            tempo_pausas_seg=18 * 60,
        )
        AgentDayStats.objects.create(
            agent=self.agent_3,
            cd_operador=self.agent_3.cd_operador,
            data_ref=self.today,
            qtd_pausas=1,
            tempo_pausas_seg=8 * 60,
        )

        # Pausas em andamento agora.
        AgentEvent.objects.create(
            source="test",
            source_event_hash="h1",
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="Banheiro",
            dt_inicio=self.now - timedelta(minutes=14),
            dt_fim=None,
            duracao_seg=None,
        )
        AgentEvent.objects.create(
            source="test",
            source_event_hash="h2",
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="Almoco",
            dt_inicio=self.now - timedelta(minutes=25),
            dt_fim=None,
            duracao_seg=None,
        )
        # Pausa finalizada (nao deve contar como atual).
        AgentEvent.objects.create(
            source="test",
            source_event_hash="h3",
            agent=self.agent_3,
            cd_operador=self.agent_3.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="Banheiro",
            dt_inicio=self.now - timedelta(minutes=40),
            dt_fim=self.now - timedelta(minutes=30),
            duracao_seg=10 * 60,
        )
        # Evento adicional de banheiro para ranking por tipo.
        AgentEvent.objects.create(
            source="test",
            source_event_hash="h4",
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="Banheiro",
            dt_inicio=self.now - timedelta(minutes=60),
            dt_fim=self.now - timedelta(minutes=40),
            duracao_seg=20 * 60,
        )

    def test_get_pause_ranking_uses_day_stats_and_overflow_limits(self):
        SystemConfig.objects.create(
            config_key="PAUSE_LIMIT_DEFAULT_MINUTES",
            config_value="10",
            value_type=SystemConfigValueType.INT,
        )

        result = get_pause_ranking(date=self.today.isoformat(), limit=2)

        self.assertEqual(result["date"], self.today.isoformat())
        self.assertEqual(result["pause_limit_minutes"], 10)
        self.assertEqual(len(result["ranking"]), 2)
        self.assertEqual(result["ranking"][0]["agent_name"], "Alice")
        self.assertEqual(result["ranking"][0]["total_minutes"], 45)
        self.assertEqual(result["ranking"][0]["overflow_minutes"], 35)

    def test_get_pause_ranking_with_pause_type_uses_events(self):
        SystemConfig.objects.create(
            config_key="PAUSE_LIMITS_JSON",
            config_value='{"banheiro": 5, "default": 10}',
            value_type=SystemConfigValueType.JSON,
        )
        result = get_pause_ranking(
            date=self.today.isoformat(),
            limit=10,
            pause_type="Banheiro",
        )

        self.assertEqual(result["pause_type"], "Banheiro")
        self.assertEqual(result["pause_limit_minutes"], 5)
        self.assertGreaterEqual(len(result["ranking"]), 1)
        self.assertEqual(result["ranking"][0]["agent_name"], "Alice")
        self.assertGreaterEqual(result["ranking"][0]["overflow_minutes"], 1)

    def test_get_current_pauses_returns_totals_and_items(self):
        result = get_current_pauses()

        self.assertEqual(result["total_in_pause"], 2)
        self.assertEqual(len(result["items"]), 2)
        pause_types = {item["pause_type"] for item in result["items"]}
        self.assertIn("Banheiro", pause_types)
        self.assertIn("Almoco", pause_types)

    def test_get_day_summary_returns_totals_and_top3(self):
        result = get_day_summary(date=self.today.isoformat())

        self.assertEqual(result["date"], self.today.isoformat())
        self.assertEqual(result["totals"]["agents_with_stats"], 3)
        self.assertEqual(result["totals"]["active_agents"], 3)
        self.assertEqual(result["totals"]["in_pause_now"], 2)
        self.assertEqual(len(result["top3"]), 3)
        self.assertEqual(result["top3"][0]["agent_name"], "Alice")
