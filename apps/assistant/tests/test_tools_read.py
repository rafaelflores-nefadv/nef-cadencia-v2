from datetime import date, datetime, timedelta
from unittest import mock

from django.test import TestCase
from django.db.utils import ProgrammingError
from django.utils import timezone

from apps.assistant.services.tools_read import (
    get_current_pauses,
    get_day_summary,
    get_pause_ranking,
    get_productivity_analytics,
)
from apps.monitoring.models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    AgentWorkday,
    PauseCategoryChoices,
    PauseClassification,
)
from apps.rules.models import SystemConfig, SystemConfigValueType


class ToolsReadTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.now = timezone.now()

        self.agent_1 = Agent.objects.create(cd_operador=1001, nm_agente="Alice")
        self.agent_2 = Agent.objects.create(cd_operador=1002, nm_agente="Bruno")
        self.agent_3 = Agent.objects.create(cd_operador=1003, nm_agente="Carla")
        self.current_tz = timezone.get_current_timezone()

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

        PauseClassification.objects.create(
            source="",
            pause_name="CAFE",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )

        self.analytics_days = [date(2026, 1, 5), date(2026, 1, 6)]
        self._create_workday(self.agent_1, self.analytics_days[0], 8)
        self._create_workday(self.agent_1, self.analytics_days[1], 8)
        self._create_workday(self.agent_2, self.analytics_days[0], 8)
        self._create_workday(self.agent_2, self.analytics_days[1], 8)
        self._create_workday(self.agent_3, self.analytics_days[0], 8)
        self._create_workday(self.agent_3, self.analytics_days[1], 8)

        self._create_period_pause_event(self.agent_1, "jan-h1", self.analytics_days[0], 60, 10)
        self._create_period_pause_event(self.agent_1, "jan-h2", self.analytics_days[1], 60, 10)
        self._create_period_pause_event(self.agent_2, "jan-h3", self.analytics_days[0], 30, 15)
        self._create_period_pause_event(self.agent_3, "jan-h4", self.analytics_days[0], 15, 20)

    def _aware_dt(self, day_ref, hour, minute=0):
        return timezone.make_aware(
            datetime(day_ref.year, day_ref.month, day_ref.day, hour, minute),
            self.current_tz,
        )

    def _create_workday(self, agent, work_date, duration_hours):
        start_dt = self._aware_dt(work_date, 8, 0)
        end_dt = start_dt + timedelta(hours=duration_hours)
        return AgentWorkday.objects.create(
            source="LH_ALIVE",
            ext_event=(agent.cd_operador * 100000) + int(work_date.strftime("%d")),
            cd_operador=agent.cd_operador,
            nm_operador=agent.nm_agente,
            work_date=work_date,
            dt_inicio=start_dt,
            dt_fim=end_dt,
            duracao_seg=int((end_dt - start_dt).total_seconds()),
        )

    def _create_period_pause_event(self, agent, source_hash, day_ref, minutes, start_hour):
        start_dt = self._aware_dt(day_ref, start_hour, 0)
        end_dt = start_dt + timedelta(minutes=minutes)
        return AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=source_hash,
            agent=agent,
            cd_operador=agent.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=start_dt,
            dt_fim=end_dt,
            duracao_seg=minutes * 60,
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

    def test_get_productivity_analytics_returns_most_improductive_agent_for_period(self):
        result = get_productivity_analytics(
            year=2026,
            month=1,
            metric="improductivity",
            group_by="agent",
            ranking_order="worst",
            limit=1,
        )

        self.assertTrue(result["dimension_available"])
        self.assertEqual(result["metric"], "improductivity")
        self.assertEqual(result["ranking"][0]["agent_name"], "Alice")
        self.assertEqual(result["ranking"][0]["tempo_improdutivo_hhmm"], "02:00:00")

    def test_get_productivity_analytics_returns_productivity_ranking(self):
        result = get_productivity_analytics(
            year=2026,
            month=1,
            metric="productivity",
            group_by="agent",
            ranking_order="best",
            limit=3,
        )

        ranking_names = [item["agent_name"] for item in result["ranking"]]
        self.assertEqual(ranking_names[0], "Carla")
        self.assertEqual(ranking_names[1], "Bruno")
        self.assertEqual(ranking_names[2], "Alice")
        self.assertEqual(result["summary"]["productivity_basis_counts"]["classified_improductivity"], 3)

    def test_get_productivity_analytics_returns_worst_productivity_ranking(self):
        result = get_productivity_analytics(
            year=2026,
            month=1,
            metric="productivity",
            group_by="agent",
            ranking_order="worst",
            limit=3,
        )

        ranking_names = [item["agent_name"] for item in result["ranking"]]
        self.assertEqual(ranking_names[0], "Alice")
        self.assertEqual(ranking_names[1], "Bruno")
        self.assertEqual(ranking_names[2], "Carla")

    def test_get_productivity_analytics_returns_dimension_unavailable_for_team(self):
        result = get_productivity_analytics(
            year=2026,
            month=1,
            metric="performance",
            group_by="team",
            ranking_order="worst",
            limit=1,
        )

        self.assertFalse(result["dimension_available"])
        self.assertEqual(result["dimension_unavailable_reason"], "team_dimension_not_available")
        self.assertEqual(result["ranking"], [])

    def test_get_productivity_analytics_returns_empty_ranking_when_period_has_no_data(self):
        result = get_productivity_analytics(
            year=2027,
            month=1,
            metric="improductivity",
            group_by="agent",
            ranking_order="worst",
            limit=10,
        )

        self.assertTrue(result["dimension_available"])
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["summary"]["total_agents_considered"], 0)
        self.assertIn("filter_without_match", result["diagnostics"])

    def test_get_productivity_analytics_uses_agent_event_fallback_for_improductivity(self):
        feb_day = date(2026, 2, 3)
        start_dt = self._aware_dt(feb_day, 9, 0)
        end_dt = start_dt + timedelta(minutes=95)
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="feb-fallback-1",
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            tp_evento="STATUS",
            nm_pausa="PAUSA DESCONHECIDA",
            dt_inicio=start_dt,
            dt_fim=end_dt,
            duracao_seg=95 * 60,
        )

        result = get_productivity_analytics(
            year=2026,
            month=2,
            metric="improductivity",
            group_by="agent",
            ranking_order="worst",
            limit=3,
        )

        self.assertTrue(result["dimension_available"])
        self.assertEqual(result["ranking"][0]["agent_name"], "Bruno")
        self.assertEqual(result["ranking"][0]["tempo_improdutivo_seg"], 95 * 60)
        self.assertIn("pause_events_raw_fallback_used", result["diagnostics"])

    def test_get_productivity_analytics_uses_data_ref_stats_without_workday(self):
        march_day = date(2026, 4, 4)
        AgentDayStats.objects.create(
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            data_ref=march_day,
            qtd_pausas=2,
            tempo_pausas_seg=30 * 60,
            ultimo_logon=self._aware_dt(march_day, 8, 0),
            ultimo_logoff=self._aware_dt(march_day, 16, 0),
        )

        result = get_productivity_analytics(
            year=2026,
            month=4,
            metric="productivity",
            group_by="agent",
            ranking_order="best",
            limit=3,
        )

        self.assertEqual(result["ranking"][0]["agent_name"], "Bruno")
        self.assertEqual(result["ranking"][0]["tempo_logado_seg"], 8 * 60 * 60)
        self.assertEqual(result["ranking"][0]["tempo_produtivo_seg"], 7 * 60 * 60 + 30 * 60)
        self.assertIn("agent_day_stats_used", result["diagnostics"])
        self.assertEqual(result["ranking"][0]["productivity_basis"], "total_pause_fallback")

    def test_get_productivity_analytics_handles_missing_agent_workday_table(self):
        with mock.patch(
            "apps.assistant.services.tools_read.AgentWorkday.objects.filter",
            side_effect=ProgrammingError("relation monitoring_agent_workday does not exist"),
        ):
            result = get_productivity_analytics(
                year=2026,
                month=1,
                metric="improductivity",
                group_by="agent",
                ranking_order="worst",
                limit=1,
            )

        self.assertEqual(result["ranking"][0]["agent_name"], "Alice")
        self.assertEqual(result["ranking"][0]["tempo_improdutivo_seg"], 2 * 60 * 60)
        self.assertIn("agent_workday_missing", result["diagnostics"])

    def test_get_productivity_analytics_handles_missing_agent_workday_table_for_productivity(self):
        march_day = date(2026, 4, 4)
        AgentDayStats.objects.create(
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            data_ref=march_day,
            qtd_pausas=2,
            tempo_pausas_seg=30 * 60,
            ultimo_logon=self._aware_dt(march_day, 8, 0),
            ultimo_logoff=self._aware_dt(march_day, 16, 0),
        )
        with mock.patch(
            "apps.assistant.services.tools_read.AgentWorkday.objects.filter",
            side_effect=ProgrammingError("relation monitoring_agent_workday does not exist"),
        ):
            result = get_productivity_analytics(
                year=2026,
                month=4,
                metric="productivity",
                group_by="agent",
                ranking_order="best",
                limit=3,
            )

        self.assertEqual(result["ranking"][0]["agent_name"], "Bruno")
        self.assertEqual(result["ranking"][0]["tempo_produtivo_seg"], 7 * 60 * 60 + 30 * 60)
        self.assertIn("agent_workday_missing", result["diagnostics"])

    def test_get_productivity_analytics_uses_event_span_fallback_for_productivity(self):
        may_day = date(2026, 5, 5)
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-a-start",
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            tp_evento="STATUS",
            nm_pausa=None,
            dt_inicio=self._aware_dt(may_day, 8, 0),
            dt_fim=None,
            duracao_seg=None,
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-a-pause",
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=self._aware_dt(may_day, 10, 0),
            dt_fim=self._aware_dt(may_day, 11, 0),
            duracao_seg=60 * 60,
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-a-end",
            agent=self.agent_1,
            cd_operador=self.agent_1.cd_operador,
            tp_evento="STATUS",
            nm_pausa=None,
            dt_inicio=self._aware_dt(may_day, 16, 0),
            dt_fim=None,
            duracao_seg=None,
        )

        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-b-start",
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            tp_evento="STATUS",
            nm_pausa=None,
            dt_inicio=self._aware_dt(may_day, 8, 0),
            dt_fim=None,
            duracao_seg=None,
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-b-pause",
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            tp_evento="PAUSA",
            nm_pausa="CAFE",
            dt_inicio=self._aware_dt(may_day, 13, 0),
            dt_fim=self._aware_dt(may_day, 13, 30),
            duracao_seg=30 * 60,
        )
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash="may-span-b-end",
            agent=self.agent_2,
            cd_operador=self.agent_2.cd_operador,
            tp_evento="STATUS",
            nm_pausa=None,
            dt_inicio=self._aware_dt(may_day, 17, 0),
            dt_fim=None,
            duracao_seg=None,
        )

        with mock.patch(
            "apps.assistant.services.tools_read.AgentWorkday.objects.filter",
            side_effect=ProgrammingError("relation monitoring_agent_workday does not exist"),
        ):
            result = get_productivity_analytics(
                year=2026,
                month=5,
                metric="productivity",
                group_by="agent",
                ranking_order="best",
                limit=5,
            )

        self.assertTrue(result["ranking"])
        self.assertEqual(result["ranking"][0]["agent_name"], "Bruno")
        self.assertEqual(result["ranking"][0]["tempo_logado_seg"], 9 * 60 * 60)
        self.assertEqual(result["ranking"][0]["tempo_produtivo_seg"], 8 * 60 * 60 + 30 * 60)
        self.assertEqual(result["ranking"][0]["logged_source"], "event_span")
        self.assertEqual(result["summary"]["logged_source_counts"]["event_span"], 2)
        self.assertEqual(result["reason_no_data"], None)
        self.assertIn("agent_workday_missing", result["diagnostics"])

    def test_get_productivity_analytics_returns_real_period_ranking_for_january_2026_style_case(self):
        january_day = date(2026, 1, 8)
        self._create_period_pause_event(self.agent_1, "jan-extra-a", january_day, 80, 9)
        self._create_period_pause_event(self.agent_2, "jan-extra-b", january_day, 45, 10)
        self._create_period_pause_event(self.agent_3, "jan-extra-c", january_day, 25, 11)

        result = get_productivity_analytics(
            year=2026,
            month=1,
            metric="improductivity",
            group_by="agent",
            ranking_order="worst",
            limit=3,
        )

        self.assertEqual(result["ranking"][0]["agent_name"], "Alice")
        self.assertEqual(result["ranking"][0]["tempo_improdutivo_seg"], (60 + 60 + 80) * 60)
        self.assertGreaterEqual(len(result["ranking"]), 3)
