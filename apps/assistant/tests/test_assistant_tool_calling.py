import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.assistant.models import AssistantActionLog, AssistantAuditLog, AssistantConversation
from apps.assistant.services.assistant_config import (
    ASSISTANT_NO_DATA_RESPONSE,
    ASSISTANT_QUERY_FAILURE_RESPONSE,
    ASSISTANT_UNVERIFIED_RESPONSE,
)


User = get_user_model()


class AssistantToolCallingIntegrationTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="tool_user", password=self.password)
        self.chat_url = reverse("assistant-chat")

    def test_chat_executes_tool_and_returns_final_answer(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_pause_ranking",
                    call_id="call_1",
                    arguments='{"date":"2026-03-05","limit":5}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Ranking operacional concluido para o dashboard.",
            output=[],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date": "2026-03-05",
                "ranking": [{"agent_id": 1, "agent_name": "Alice", "total_minutes": 30}],
            },
        ) as mocked_execute_tool:
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Quem mais estourou pausa hoje?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], "Ranking operacional concluido para o dashboard.")
        mocked_execute_tool.assert_called_once()
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        log = AssistantActionLog.objects.first()
        self.assertEqual(log.tool_name, "get_pause_ranking")
        self.assertEqual(log.status, "success")

    def test_chat_returns_no_data_response_when_supported_query_has_no_data(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_pause_ranking",
                    call_id="call_1",
                    arguments='{"date":"2026-03-05","limit":5}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Nao encontrei nada.",
            output=[],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={"date": "2026-03-05", "ranking": []},
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Quem mais estourou pausa hoje?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_NO_DATA_RESPONSE)
        self.assertIn("Eust\u00e1cio", payload["answer"])

    def test_chat_blocks_model_that_claims_action_completed_without_tool(self):
        mock_client = Mock()
        mock_client.responses.create.return_value = SimpleNamespace(
            output_text="Ja enviei a mensagem para o agente.",
            output=[],
        )

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Envie mensagem para o agente A"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_UNVERIFIED_RESPONSE)
        self.assertIn("Eust\u00e1cio", payload["answer"])

    def test_chat_returns_query_failure_when_tool_execution_errors(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_pause_ranking",
                    call_id="call_1",
                    arguments='{"date":"2026-03-05","limit":5}',
                )
            ],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=RuntimeError("tool exploded"),
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Quem mais estourou pausa hoje?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_QUERY_FAILURE_RESPONSE)
        self.assertIn("Eust\u00e1cio", payload["answer"])
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        log = AssistantActionLog.objects.first()
        self.assertEqual(log.tool_name, "get_pause_ranking")
        self.assertEqual(log.status, "error")

    def test_chat_executes_productivity_analytics_for_most_improductive_agent(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"year":2026,"month":1,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":1}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Nao encontrei dados suficientes para esse periodo.",
            output=[],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "period_label": "01/01/2026 ate 31/01/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "dimension_available": True,
                "ranking": [
                    {
                        "agent_id": 1,
                        "cd_operador": 1001,
                        "agent_name": "Alice",
                        "tempo_improdutivo_seg": 7200,
                        "tempo_improdutivo_hhmm": "02:00:00",
                        "tempo_produtivo_seg": 21600,
                        "tempo_produtivo_hhmm": "06:00:00",
                        "taxa_ocupacao_pct": 75.0,
                    }
                ],
                "summary": {
                    "total_agents_considered": 3,
                    "total_logged_seconds": 86400,
                    "total_productive_seconds": 75600,
                    "total_improductive_seconds": 10800,
                    "total_pause_seconds": 10800,
                },
            },
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual o agente mais improdutivo de janeiro de 2026?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Alice", response.json()["answer"])
        self.assertIn("01/01/2026 ate 31/01/2026", response.json()["answer"])
        self.assertNotIn("nao encontrei dados suficientes", response.json()["answer"].lower())
        self.assertEqual(response.json()["answer_payload"]["type"], "ranking")
        self.assertEqual(
            response.json()["answer_payload"]["title"],
            "Top 1 agente mais improdutivo",
        )
        self.assertEqual(
            response.json()["answer_payload"]["items"][0]["value"],
            "02:00:00",
        )
        self.assertEqual(
            [item["status"] for item in response.json()["processing_statuses"]],
            [
                "understanding_query",
                "checking_context",
                "resolving_intent",
                "querying_database",
                "running_tool",
                "filtering_results",
                "building_response",
                "validating_response",
                "completed",
            ],
        )
        log = AssistantActionLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.tool_name, "get_productivity_analytics")
        self.assertEqual(log.status, "success")
        conversation = AssistantConversation.objects.get(pk=response.json()["conversation_id"])
        assistant_message = conversation.messages.order_by("created_at", "id").last()
        self.assertEqual(assistant_message.payload_json["type"], "ranking")
        self.assertEqual(
            assistant_message.payload_json["items"][0]["name"],
            "Alice",
        )

    def test_chat_returns_no_data_for_team_performance_without_team_dimension(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"period_key":"last_month","metric":"performance","group_by":"team","ranking_order":"worst","limit":1}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Nao encontrei equipes no periodo.",
            output=[],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date_from": "2026-02-01",
                "date_to": "2026-02-28",
                "period_label": "01/02/2026 ate 28/02/2026",
                "metric": "performance",
                "group_by": "team",
                "ranking_order": "worst",
                "dimension_available": False,
                "dimension_unavailable_reason": "team_dimension_not_available",
                "ranking": [],
                "summary": {"total_agents_considered": 4},
            },
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual equipe teve pior desempenho no mes passado?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nao encontrei dados de produtividade", response.json()["answer"])
        self.assertIn("Posso tentar novamente", response.json()["answer"])

    def test_chat_returns_no_data_when_productivity_analytics_has_real_empty_ranking(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"year":2026,"month":1,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":1}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Talvez nao haja dados.",
            output=[],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "period_label": "01/01/2026 ate 31/01/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "dimension_available": True,
                "ranking": [],
                "summary": {"total_agents_considered": 0},
                "reason_no_data": "filter_without_match",
            },
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual o agente mais improdutivo de janeiro de 2026?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nao encontrei dados de produtividade", response.json()["answer"])
        self.assertIn("Posso tentar novamente", response.json()["answer"])

    def test_chat_reuses_previous_productivity_period_for_follow_up_question(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"year":2026,"month":1,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":1}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])
        third_response = SimpleNamespace(
            id="resp_3",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_2",
                    arguments='{"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":10}',
                )
            ],
        )
        fourth_response = SimpleNamespace(id="resp_4", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            first_response,
            second_response,
            third_response,
            fourth_response,
        ]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            if args.get("limit") == 1:
                return {
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                    "period_label": "01/01/2026 ate 31/01/2026",
                    "metric": "improductivity",
                    "group_by": "agent",
                    "ranking_order": "worst",
                    "limit": 1,
                    "dimension_available": True,
                    "ranking": [
                        {
                            "agent_id": 1,
                            "cd_operador": 1001,
                            "agent_name": "Alice",
                            "tempo_improdutivo_hhmm": "02:00:00",
                            "tempo_improdutivo_seg": 7200,
                        }
                    ],
                    "summary": {"total_agents_considered": 3},
                }
            return {
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "period_label": "01/01/2026 ate 31/01/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:00:00"},
                    {"agent_name": "Bruno", "tempo_improdutivo_hhmm": "01:30:00"},
                    {"agent_name": "Carla", "tempo_improdutivo_hhmm": "01:00:00"},
                ],
                "summary": {"total_agents_considered": 3},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            first_http_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual o agente mais improdutivo de janeiro de 2026?"}),
                content_type="application/json",
            )
            conversation_id = first_http_response.json()["conversation_id"]
            second_http_response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "qual o top 10 de improdutivos?",
                        "conversation_id": conversation_id,
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(first_http_response.status_code, 200)
        self.assertEqual(second_http_response.status_code, 200)
        self.assertEqual(recorded_args[1][1]["date_from"], "2026-01-01")
        self.assertEqual(recorded_args[1][1]["date_to"], "2026-01-31")
        self.assertEqual(recorded_args[1][1]["limit"], 10)
        self.assertIn("Top 3 de improdutividade", second_http_response.json()["answer"])
        self.assertIn("Alice", second_http_response.json()["answer"])

        conversation = AssistantConversation.objects.get(pk=conversation_id)
        self.assertEqual(
            conversation.context_json["productivity_analytics"]["start_date"],
            "2026-01-01",
        )
        self.assertEqual(
            conversation.context_json["productivity_analytics"]["end_date"],
            "2026-01-31",
        )

    def test_chat_explicit_new_period_overrides_previous_productivity_context(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"year":2026,"month":1,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":1}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])
        third_response = SimpleNamespace(
            id="resp_3",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_2",
                    arguments='{"year":2026,"month":2,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":10}',
                )
            ],
        )
        fourth_response = SimpleNamespace(id="resp_4", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            first_response,
            second_response,
            third_response,
            fourth_response,
        ]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            if args.get("month") == 1:
                return {
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                    "period_label": "01/01/2026 ate 31/01/2026",
                    "metric": "improductivity",
                    "group_by": "agent",
                    "ranking_order": "worst",
                    "limit": 1,
                    "dimension_available": True,
                    "ranking": [{"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:00:00"}],
                    "summary": {"total_agents_considered": 3},
                }
            return {
                "date_from": "2026-02-01",
                "date_to": "2026-02-28",
                "period_label": "01/02/2026 ate 28/02/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [{"agent_name": "Bruno", "tempo_improdutivo_hhmm": "01:45:00"}],
                "summary": {"total_agents_considered": 3},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            first_http_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual o agente mais improdutivo de janeiro de 2026?"}),
                content_type="application/json",
            )
            conversation_id = first_http_response.json()["conversation_id"]
            second_http_response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "qual o top 10 de improdutivos de fevereiro de 2026?",
                        "conversation_id": conversation_id,
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(second_http_response.status_code, 200)
        self.assertEqual(recorded_args[1][1]["year"], 2026)
        self.assertEqual(recorded_args[1][1]["month"], 2)
        self.assertNotEqual(recorded_args[1][1].get("date_from"), "2026-01-01")
        self.assertIn("01/02/2026 ate 28/02/2026", second_http_response.json()["answer"])

    def test_chat_follow_up_without_previous_context_does_not_inject_old_period(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":10}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            return {
                "date_from": "2026-03-01",
                "date_to": "2026-03-09",
                "period_label": "01/03/2026 ate 09/03/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [{"agent_name": "Carla", "tempo_improdutivo_hhmm": "01:00:00"}],
                "summary": {"total_agents_considered": 1},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "qual o top 10 de improdutivos?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("date_from", recorded_args[0][1])
        self.assertNotIn("date_to", recorded_args[0][1])
        self.assertIn("01/03/2026 ate 09/03/2026", response.json()["answer"])

    def test_chat_follow_up_switches_metric_and_preserves_period_and_limit(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"date_from":"2026-01-01","date_to":"2026-03-10","metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":5}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])
        third_response = SimpleNamespace(
            id="resp_3",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_2",
                    arguments="{}",
                )
            ],
        )
        fourth_response = SimpleNamespace(id="resp_4", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            first_response,
            second_response,
            third_response,
            fourth_response,
        ]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            if args.get("metric") == "productivity":
                return {
                    "date_from": "2026-01-01",
                    "date_to": "2026-03-10",
                    "period_label": "01/01/2026 ate 10/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "limit": 5,
                    "dimension_available": True,
                    "ranking": [
                        {"agent_name": "Bruno", "tempo_produtivo_hhmm": "08:30:00"},
                        {"agent_name": "Carla", "tempo_produtivo_hhmm": "08:00:00"},
                    ],
                    "summary": {"total_agents_considered": 2},
                }
            return {
                "date_from": "2026-01-01",
                "date_to": "2026-03-10",
                "period_label": "01/01/2026 ate 10/03/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 5,
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:10:00"},
                    {"agent_name": "Bruno", "tempo_improdutivo_hhmm": "01:55:00"},
                ],
                "summary": {"total_agents_considered": 2},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            first_http_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Pode me informar os 5 piores agentes do ano?"}),
                content_type="application/json",
            )
            conversation_id = first_http_response.json()["conversation_id"]
            second_http_response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "Quais os 5 agentes mais produtivos?",
                        "conversation_id": conversation_id,
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(second_http_response.status_code, 200)
        second_payload = second_http_response.json()
        self.assertEqual(recorded_args[1][1]["date_from"], "2026-01-01")
        self.assertEqual(recorded_args[1][1]["date_to"], "2026-03-10")
        self.assertEqual(recorded_args[1][1]["group_by"], "agent")
        self.assertEqual(recorded_args[1][1]["limit"], 5)
        self.assertEqual(recorded_args[1][1]["metric"], "productivity")
        self.assertEqual(recorded_args[1][1]["ranking_order"], "best")
        self.assertIn("Top 2 de produtividade", second_payload["answer"])
        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertEqual(audit.pipeline_trace_json["question"], "Quais os 5 agentes mais produtivos?")
        self.assertEqual(
            audit.pipeline_trace_json["resolved_context"]["context_before"]["productivity_context"]["start_date"],
            "2026-01-01",
        )
        self.assertEqual(
            audit.pipeline_trace_json["resolved_context"]["context_before"]["productivity_context"]["end_date"],
            "2026-03-10",
        )
        self.assertEqual(
            audit.pipeline_trace_json["resolved_context"]["semantic_resolution"]["tool_args"]["date_from"],
            "2026-01-01",
        )
        self.assertEqual(
            audit.pipeline_trace_json["resolved_context"]["semantic_resolution"]["tool_args"]["date_to"],
            "2026-03-10",
        )
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_productivity_analytics")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_from"], "2026-01-01")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_to"], "2026-03-10")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["group_by"], "agent")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["limit"], 5)
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["metric"], "productivity")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["ranking_order"], "best")
        self.assertEqual(audit.pipeline_trace_json["tool_result_rows"], 2)
        self.assertEqual(
            audit.pipeline_trace_json["tool_result_preview"]["summary"]["total_agents_considered"],
            2,
        )
        self.assertEqual(audit.pipeline_trace_json["reason_no_data"], "")
        self.assertEqual(audit.pipeline_trace_json["final_answer_type"], "backend_deterministic")
        self.assertEqual(audit.pipeline_trace_json["exception"], "")
        self.assertNotEqual(audit.pipeline_trace_json["tool_result_rows"], 0)
        self.assertNotEqual(audit.pipeline_trace_json["final_answer_type"], "no_data")
        self.assertNotEqual(audit.pipeline_trace_json["final_answer_type"], "assistant_runtime_error")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 10))
    def test_chat_follow_up_best_keeps_month_without_year_context(self, _mocked_today):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"year":2026,"month":1,"metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":10}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])
        third_response = SimpleNamespace(
            id="resp_3",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_2",
                    arguments="{}",
                )
            ],
        )
        fourth_response = SimpleNamespace(id="resp_4", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            first_response,
            second_response,
            third_response,
            fourth_response,
        ]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            if args.get("ranking_order") == "best":
                return {
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                    "period_label": "01/01/2026 ate 31/01/2026",
                    "metric": "improductivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "limit": 10,
                    "dimension_available": True,
                    "ranking": [{"agent_name": "Bruno", "tempo_improdutivo_hhmm": "00:40:00"}],
                    "summary": {"total_agents_considered": 2},
                }
            return {
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "period_label": "01/01/2026 ate 31/01/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [{"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:00:00"}],
                "summary": {"total_agents_considered": 2},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            first_http_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "10 piores agentes de janeiro"}),
                content_type="application/json",
            )
            conversation_id = first_http_response.json()["conversation_id"]
            second_http_response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "e os melhores?",
                        "conversation_id": conversation_id,
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(second_http_response.status_code, 200)
        self.assertEqual(recorded_args[1][1]["date_from"], "2026-01-01")
        self.assertEqual(recorded_args[1][1]["date_to"], "2026-01-31")
        self.assertEqual(recorded_args[1][1]["limit"], 10)
        self.assertEqual(recorded_args[1][1]["ranking_order"], "best")
        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_from"], "2026-01-01")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_to"], "2026-01-31")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["limit"], 10)
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["ranking_order"], "best")

    def test_chat_follow_up_better_this_month_keeps_thread_context(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"date_from":"2026-03-01","date_to":"2026-03-09","metric":"improductivity","group_by":"agent","ranking_order":"worst","limit":10}',
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])
        third_response = SimpleNamespace(
            id="resp_3",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_2",
                    arguments="{}",
                )
            ],
        )
        fourth_response = SimpleNamespace(id="resp_4", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            first_response,
            second_response,
            third_response,
            fourth_response,
        ]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            if args.get("metric") == "productivity":
                return {
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-09",
                    "period_label": "01/03/2026 ate 09/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "limit": 10,
                    "dimension_available": True,
                    "ranking": [{"agent_name": "Carla", "tempo_produtivo_hhmm": "07:30:00"}],
                    "summary": {"total_agents_considered": 1},
                }
            return {
                "date_from": "2026-03-01",
                "date_to": "2026-03-09",
                "period_label": "01/03/2026 ate 09/03/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [{"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:10:00"}],
                "summary": {"total_agents_considered": 1},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            first_http_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "quem esta pior esse mes"}),
                content_type="application/json",
            )
            conversation_id = first_http_response.json()["conversation_id"]
            second_http_response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "quem esta melhor?",
                        "conversation_id": conversation_id,
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(second_http_response.status_code, 200)
        self.assertEqual(recorded_args[1][1]["date_from"], "2026-03-01")
        self.assertEqual(recorded_args[1][1]["date_to"], "2026-03-09")
        self.assertEqual(recorded_args[1][1]["metric"], "productivity")
        self.assertEqual(recorded_args[1][1]["ranking_order"], "best")
        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_from"], "2026-03-01")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["date_to"], "2026-03-09")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["metric"], "productivity")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["ranking_order"], "best")

    def test_chat_understands_semantic_worst_agents_question(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments="{}",
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            return {
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "period_label": "01/01/2026 ate 31/01/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 10,
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_improdutivo_hhmm": "02:00:00"},
                    {"agent_name": "Bruno", "tempo_improdutivo_hhmm": "01:30:00"},
                ],
                "summary": {"total_agents_considered": 2},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps(
                    {
                        "text": "Pode me dizer quem sao os piores agentes de janeiro de 2026?",
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(recorded_args[0][1]["metric"], "improductivity")
        self.assertEqual(recorded_args[0][1]["ranking_order"], "worst")
        self.assertEqual(recorded_args[0][1]["group_by"], "agent")
        self.assertEqual(recorded_args[0][1]["year"], 2026)
        self.assertEqual(recorded_args[0][1]["month"], 1)
        self.assertIn("Top 2 de improdutividade", response.json()["answer"])

    def test_chat_resolves_year_to_date_for_worst_agent_of_year(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments="{}",
                )
            ],
        )
        second_response = SimpleNamespace(id="resp_2", output_text="Resposta do modelo ignorada.", output=[])

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        recorded_args = []

        def execute_tool_side_effect(tool_name, args, user):
            recorded_args.append((tool_name, dict(args)))
            return {
                "date_from": "2026-01-01",
                "date_to": "2026-03-10",
                "period_label": "01/01/2026 ate 10/03/2026",
                "metric": "improductivity",
                "group_by": "agent",
                "ranking_order": "worst",
                "limit": 1,
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_improdutivo_hhmm": "12:00:00"},
                ],
                "summary": {"total_agents_considered": 2},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=execute_tool_side_effect,
        ), patch(
            "apps.assistant.services.semantic_resolution.timezone.localdate",
            return_value=date(2026, 3, 10),
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "quem esta sendo o pior agente do ano?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(recorded_args[0][1]["date_from"], "2026-01-01")
        self.assertEqual(recorded_args[0][1]["date_to"], "2026-03-10")
        self.assertIn("01/01/2026 ate 10/03/2026", response.json()["answer"])

    def test_chat_returns_query_failure_when_productivity_analytics_tool_errors(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"metric":"productivity","group_by":"agent","limit":10}',
                )
            ],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response]

        self.client.login(username=self.user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=RuntimeError("analytics exploded"),
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "ranking de produtividade dos agentes"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], ASSISTANT_QUERY_FAILURE_RESPONSE)
        self.assertEqual(response.json()["processing_status"], "failed")
        self.assertIn(
            "failed",
            [item["status"] for item in response.json()["processing_statuses"]],
        )
        log = AssistantActionLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.tool_name, "get_productivity_analytics")
        self.assertEqual(log.status, "error")
