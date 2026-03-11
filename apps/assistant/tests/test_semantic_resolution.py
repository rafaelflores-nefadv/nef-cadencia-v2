from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.assistant.services.semantic_resolution import resolve_semantic_operational_query


class AssistantSemanticResolutionTests(SimpleTestCase):
    def test_understands_worst_agents_historical_question(self):
        resolution = resolve_semantic_operational_query(
            "quem sao os piores agentes de janeiro de 2026?"
        )

        self.assertTrue(resolution.semantic_applied)
        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "improductivity")
        self.assertEqual(resolution.ranking_order, "worst")
        self.assertEqual(resolution.subject, "agent")
        self.assertEqual(resolution.tool_args["month"], 1)
        self.assertEqual(resolution.tool_args["year"], 2026)
        self.assertEqual(resolution.limit, 10)

    def test_understands_worst_agent_singular(self):
        resolution = resolve_semantic_operational_query(
            "quem foi o pior agente de janeiro de 2026?"
        )

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.limit, 1)

    def test_understands_best_agents_of_period(self):
        resolution = resolve_semantic_operational_query("quais os melhores agentes do periodo?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "productivity")
        self.assertEqual(resolution.ranking_order, "best")

    def test_understands_worst_performance(self):
        resolution = resolve_semantic_operational_query("quem teve o pior desempenho?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "performance")
        self.assertEqual(resolution.ranking_order, "worst")

    def test_understands_produtividade_fraca(self):
        resolution = resolve_semantic_operational_query("quem esta com produtividade fraca?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "improductivity")
        self.assertEqual(resolution.ranking_order, "worst")

    def test_understands_rendendo_bem(self):
        resolution = resolve_semantic_operational_query("quem esta rendendo bem?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "productivity")
        self.assertEqual(resolution.ranking_order, "best")

    def test_understands_compensando_operacao_as_business_rule(self):
        resolution = resolve_semantic_operational_query("quem esta compensando a operacao?")

        self.assertTrue(resolution.semantic_applied)
        self.assertEqual(resolution.intent, "business_rule_query")
        self.assertEqual(resolution.business_rule, "se_pagando_em_tempo")
        self.assertTrue(resolution.needs_business_definition)

    def test_understands_valendo_o_custo_as_business_rule(self):
        resolution = resolve_semantic_operational_query("quem esta valendo o custo?")

        self.assertEqual(resolution.intent, "business_rule_query")
        self.assertEqual(resolution.business_rule, "se_pagando_em_tempo")

    def test_understands_ocioso_alto_as_performance_signal(self):
        resolution = resolve_semantic_operational_query("quem esta com ocioso alto?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "performance")
        self.assertEqual(resolution.ranking_order, "worst")

    def test_understands_abaixo_da_regua_as_performance_signal(self):
        resolution = resolve_semantic_operational_query("quem esta abaixo da regua?")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "performance")
        self.assertEqual(resolution.ranking_order, "worst")

    def test_understands_segurando_meta_as_business_rule(self):
        resolution = resolve_semantic_operational_query("quem esta segurando a meta?")

        self.assertEqual(resolution.intent, "business_rule_query")
        self.assertEqual(resolution.business_rule, "segurando_meta")
        self.assertTrue(resolution.needs_business_definition)

    def test_business_jargon_requires_definition(self):
        resolution = resolve_semantic_operational_query("quem esta se pagando em tempo?")

        self.assertTrue(resolution.needs_business_definition)
        self.assertEqual(resolution.business_rule, "se_pagando_em_tempo")
        self.assertIn("regra operacional cadastrada", resolution.clarification_response or "")

    def test_pause_excess_is_mapped_to_pause_ranking(self):
        resolution = resolve_semantic_operational_query("quem esta estourando pausa?")

        self.assertEqual(resolution.intent, "pause_ranking_query")
        self.assertIn("ranking de pausas", resolution.expanded_text)

    def test_ambiguous_term_requests_clarification(self):
        resolution = resolve_semantic_operational_query("quem esta folgado?")

        self.assertTrue(resolution.needs_clarification)
        self.assertIn("ambiguo", resolution.clarification_response or "")

    def test_ruim_without_metric_requests_clarification(self):
        resolution = resolve_semantic_operational_query("quem esta ruim?")

        self.assertTrue(resolution.needs_clarification)
        self.assertEqual(resolution.intent, "clarification_query")

    def test_forte_without_metric_requests_clarification(self):
        resolution = resolve_semantic_operational_query("quem esta forte?")

        self.assertTrue(resolution.needs_clarification)
        self.assertEqual(resolution.intent, "clarification_query")

    def test_follow_up_reuses_previous_context(self):
        resolution = resolve_semantic_operational_query(
            "e os melhores?",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 10,
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                }
            },
        )

        self.assertTrue(resolution.reused_context)
        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.ranking_order, "best")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-01-31")

    def test_follow_up_changes_only_limit(self):
        resolution = resolve_semantic_operational_query(
            "agora o top 5",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 10,
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                }
            },
        )

        self.assertEqual(resolution.tool_args["limit"], 5)
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.metric, "improductivity")

    def test_follow_up_flips_polarity_from_previous_context(self):
        resolution = resolve_semantic_operational_query(
            "e os melhores?",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 10,
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                }
            },
        )

        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-01-31")
        self.assertEqual(resolution.ranking_order, "best")

    def test_follow_up_switches_to_more_productive_and_keeps_period_and_limit(self):
        resolution = resolve_semantic_operational_query(
            "quais os 5 agentes mais produtivos?",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 5,
                    "date_from": "2026-01-01",
                    "date_to": "2026-03-10",
                }
            },
        )

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "productivity")
        self.assertEqual(resolution.ranking_order, "best")
        self.assertEqual(resolution.tool_args["limit"], 5)
        self.assertEqual(resolution.subject, "agent")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    def test_follow_up_keeps_previous_limit_when_only_best_is_requested(self):
        resolution = resolve_semantic_operational_query(
            "e os melhores?",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 5,
                    "date_from": "2026-01-01",
                    "date_to": "2026-03-10",
                }
            },
        )

        self.assertEqual(resolution.tool_args["limit"], 5)
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    def test_follow_up_overrides_period(self):
        resolution = resolve_semantic_operational_query(
            "e no mes passado?",
            {
                "semantic_operational": {
                    "intent": "productivity_analytics_query",
                    "subject": "agent",
                    "metric": "improductivity",
                    "ranking_order": "worst",
                    "limit": 10,
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                }
            },
        )

        self.assertEqual(resolution.tool_args["period_key"], "last_month")
        self.assertNotIn("date_from", resolution.tool_args)

    def test_external_domain_is_not_semantically_normalized(self):
        resolution = resolve_semantic_operational_query("quem sao os piores presidentes da historia?")

        self.assertFalse(resolution.semantic_applied)

    def test_market_language_stays_out_of_domain(self):
        resolution = resolve_semantic_operational_query("quais empresas estao se pagando no mercado?")

        self.assertFalse(resolution.semantic_applied)

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_worst_agent_of_year_uses_year_to_date(self, _mocked_today):
        resolution = resolve_semantic_operational_query("pior agente do ano")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.ranking_order, "worst")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_best_agent_of_year_uses_year_to_date(self, _mocked_today):
        resolution = resolve_semantic_operational_query("melhor agente do ano")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.ranking_order, "best")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_improductivity_ranking_of_year_uses_year_to_date(self, _mocked_today):
        resolution = resolve_semantic_operational_query("ranking de improdutividade do ano")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.metric, "improductivity")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_who_is_worse_this_year_uses_year_to_date(self, _mocked_today):
        resolution = resolve_semantic_operational_query("quem esta pior esse ano")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.ranking_order, "worst")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_who_is_better_this_year_uses_year_to_date(self, _mocked_today):
        resolution = resolve_semantic_operational_query("quem esta melhor esse ano")

        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.ranking_order, "best")
        self.assertEqual(resolution.tool_args["date_from"], "2026-01-01")
        self.assertEqual(resolution.tool_args["date_to"], "2026-03-10")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_explicit_month_still_wins_over_generic_year_language(self, _mocked_today):
        resolution = resolve_semantic_operational_query("pior agente de janeiro de 2026 desse ano")

        self.assertEqual(resolution.tool_args["year"], 2026)
        self.assertEqual(resolution.tool_args["month"], 1)
        self.assertNotIn("date_from", resolution.tool_args)

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_month_without_year_uses_current_year(self, _mocked_today):
        resolution = resolve_semantic_operational_query("10 piores agentes de janeiro")

        self.assertEqual(resolution.tool_args["year"], 2026)
        self.assertEqual(resolution.tool_args["month"], 1)
        self.assertEqual(resolution.tool_args["limit"], 10)
