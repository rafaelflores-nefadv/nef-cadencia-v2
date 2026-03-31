from django.test import SimpleTestCase

from apps.assistant.services.semantic_intent import normalize_semantic_intent


class AssistantSemanticIntentTests(SimpleTestCase):
    def test_worst_agents_in_january_maps_to_productivity_analytics(self):
        result = normalize_semantic_intent(
            "Pode me dizer quem sao os piores agentes de janeiro de 2026?"
        )

        self.assertEqual(result.capability_id, "productivity_analytics_query")
        self.assertEqual(result.tool_args["metric"], "improductivity")
        self.assertEqual(result.tool_args["ranking_order"], "worst")
        self.assertEqual(result.tool_args["group_by"], "agent")
        self.assertEqual(result.tool_args["year"], 2026)
        self.assertEqual(result.tool_args["month"], 1)

    def test_worst_agent_singular_maps_to_limit_one(self):
        result = normalize_semantic_intent(
            "quem foi o pior agente de janeiro de 2026?"
        )

        self.assertEqual(result.capability_id, "productivity_analytics_query")
        self.assertEqual(result.tool_args["limit"], 1)

    def test_best_agents_of_period_maps_to_best_productivity(self):
        result = normalize_semantic_intent("quais os melhores agentes do periodo?")

        self.assertEqual(result.capability_id, "productivity_analytics_query")
        self.assertEqual(result.tool_args["metric"], "productivity")
        self.assertEqual(result.tool_args["ranking_order"], "best")

    def test_worst_performance_maps_to_performance_metric(self):
        result = normalize_semantic_intent("quem teve o pior desempenho?")

        self.assertEqual(result.capability_id, "productivity_analytics_query")
        self.assertEqual(result.tool_args["metric"], "performance")
        self.assertEqual(result.tool_args["ranking_order"], "worst")

    def test_follow_up_uses_previous_context_and_limit(self):
        result = normalize_semantic_intent(
            "me mostra os 10 piores",
            {
                "productivity_analytics": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31",
                    "metric": "improductivity",
                    "group_by": "agent",
                    "ranking_order": "worst",
                    "limit": 1,
                }
            },
        )

        self.assertEqual(result.capability_id, "productivity_analytics_query")
        self.assertEqual(result.tool_args["date_from"], "2026-01-01")
        self.assertEqual(result.tool_args["date_to"], "2026-01-31")
        self.assertEqual(result.tool_args["limit"], 10)

    def test_external_context_does_not_activate_semantic_analytics(self):
        result = normalize_semantic_intent("quem sao os piores agentes da economia mundial?")

        self.assertIsNone(result.capability_id)
