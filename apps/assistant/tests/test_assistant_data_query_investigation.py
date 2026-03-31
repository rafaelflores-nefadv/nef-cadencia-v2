import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.assistant.models import AssistantActionLog, AssistantAuditLog, AssistantConversationOrigin
from apps.assistant.services.assistant_service import (
    _build_productivity_analytics_response,
    _build_responses_input_from_messages,
    run_chat,
)
from apps.assistant.services.capabilities import CONSULTA_SUPORTADA, assess_capability
from apps.assistant.services.semantic_resolution import resolve_semantic_operational_query
from apps.assistant.services.tool_registry import (
    TOOL_GET_AGENTS_LISTING,
    TOOL_GET_PRODUCTIVITY_ANALYTICS,
    get_tools_schema,
)


User = get_user_model()


class AssistantDataQueryRoutingInvestigationTests(SimpleTestCase):
    def test_group_a_listing_questions_map_to_agent_listing_query(self):
        questions = [
            "Liste os agentes cadastrados",
            "Quais agentes existem no sistema?",
            "Quais agentes estao ativos?",
            "Mostre os agentes",
        ]
        for question in questions:
            with self.subTest(question=question):
                assessment = assess_capability(question)
                self.assertEqual(assessment.category, CONSULTA_SUPORTADA)
                self.assertEqual(assessment.capability_id, "agent_listing_query")
                self.assertEqual(assessment.allowed_tools, (TOOL_GET_AGENTS_LISTING,))

    def test_group_b_analytics_questions_map_to_productivity_analytics_query(self):
        questions = [
            "Quais os agentes produtivos?",
            "Quem sao os agentes mais produtivos?",
            "Me mostra os agentes com maior produtividade",
            "Quais agentes tiveram melhor produtividade?",
            "Quais os agentes mais produtivos hoje?",
            "Ranking de produtividade dos agentes",
            "Quem produziu mais esta semana?",
        ]
        for question in questions:
            with self.subTest(question=question):
                assessment = assess_capability(question)
                self.assertEqual(assessment.category, CONSULTA_SUPORTADA)
                self.assertEqual(assessment.capability_id, "productivity_analytics_query")
                self.assertEqual(
                    assessment.allowed_tools,
                    (TOOL_GET_PRODUCTIVITY_ANALYTICS,),
                )

    def test_group_c_combined_active_productivity_question_maps_to_analytics(self):
        resolution = resolve_semantic_operational_query("Quais os agentes ativos e produtivos?")

        self.assertTrue(resolution.semantic_applied)
        self.assertFalse(resolution.needs_clarification)
        self.assertEqual(resolution.intent, "productivity_analytics_query")
        self.assertEqual(resolution.tool_args.get("only_active"), True)

    def test_group_c_explicit_or_between_active_and_productive_still_requests_clarification(self):
        resolution = resolve_semantic_operational_query("Quero ver os agentes ativos ou os produtivos")

        self.assertTrue(resolution.semantic_applied)
        self.assertTrue(resolution.needs_clarification)
        self.assertEqual(resolution.intent, "agent_productivity_ambiguity")

    def test_tools_schema_exposes_agents_listing_tool(self):
        tool_names = [item.get("name") for item in get_tools_schema()]

        self.assertIn(TOOL_GET_AGENTS_LISTING, tool_names)
        self.assertIn(TOOL_GET_PRODUCTIVITY_ANALYTICS, tool_names)


class AssistantResponsesPayloadSchemaTests(SimpleTestCase):
    def test_history_serialization_uses_output_text_for_assistant_messages(self):
        payload = _build_responses_input_from_messages(
            [
                {"role": "user", "content": "Primeira pergunta"},
                {"role": "assistant", "content": "Primeira resposta"},
                {"role": "user", "content": "Segunda pergunta"},
            ]
        )

        history_items = [item for item in payload if item.get("role") in {"user", "assistant"}]
        self.assertEqual([item.get("role") for item in history_items], ["user", "assistant", "user"])
        self.assertEqual(history_items[0]["content"][0]["type"], "input_text")
        self.assertEqual(history_items[1]["content"][0]["type"], "output_text")
        self.assertEqual(history_items[2]["content"][0]["type"], "input_text")

    def test_assistant_refusal_metadata_is_serialized_as_refusal(self):
        payload = _build_responses_input_from_messages(
            [
                {
                    "role": "assistant",
                    "content": "Nao posso responder a essa solicitacao.",
                    "metadata": {
                        "content_type": "refusal",
                        "refusal": "Nao posso responder a essa solicitacao.",
                    },
                }
            ]
        )

        assistant_item = next(item for item in payload if item.get("role") == "assistant")
        self.assertEqual(assistant_item["content"][0]["type"], "refusal")
        self.assertEqual(
            assistant_item["content"][0]["refusal"],
            "Nao posso responder a essa solicitacao.",
        )


class AssistantDataQueryRuntimeInvestigationTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="invest_data_user", password=self.password)
        self.chat_url = reverse("assistant-chat")
        self.client.login(username=self.user.username, password=self.password)

    def _mock_openai_client_with_responses(self, responses):
        mock_client = Mock()
        mock_client.responses.create.side_effect = responses
        return patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        )

    def _post_chat(self, text: str, conversation_id: int | None = None):
        payload = {"text": text}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        return self.client.post(
            self.chat_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_group_a_listing_executes_agent_listing_tool_and_returns_data(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_agents_listing",
                    call_id="call_1",
                    arguments='{"only_active":true,"limit":10}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="Resposta do modelo ignorada por resposta deterministica.",
            output=[],
        )

        with self._mock_openai_client_with_responses([first_response, second_response]), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "only_active": True,
                "limit": 10,
                "total_found": 2,
                "items": [
                    {"agent_id": 1, "cd_operador": 1001, "agent_name": "Alice", "is_active": True},
                    {"agent_id": 2, "cd_operador": 1002, "agent_name": "Bruno", "is_active": True},
                ],
                "reason_no_data": None,
            },
        ):
            response = self._post_chat("Quais agentes estao ativos?")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Encontrei 2 agentes ativos", response.json()["answer"])
        self.assertIn("Alice", response.json()["answer"])

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.capability_id, "agent_listing_query")
        self.assertEqual(audit.final_response_status, "completed")
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_agents_listing")
        self.assertEqual(audit.pipeline_trace_json["tool_result_rows"], 2)
        self.assertEqual(audit.pipeline_trace_json["final_answer_type"], "backend_deterministic")

    def test_group_b_analytics_without_data_returns_clear_period_message(self):
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

        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response]
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date_from": "2026-03-30",
                "date_to": "2026-03-30",
                "period_label": "30/03/2026",
                "metric": "productivity",
                "group_by": "agent",
                "ranking_order": "best",
                "dimension_available": True,
                "ranking": [],
                "summary": {"total_agents_considered": 0},
                "reason_no_data": "filter_without_match",
            },
        ):
            response = self._post_chat("Ranking de produtividade dos agentes")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nao encontrei dados de produtividade", response.json()["answer"])
        self.assertIn("Posso tentar novamente", response.json()["answer"])
        self.assertEqual(mock_client.responses.create.call_count, 1)

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.capability_id, "productivity_analytics_query")
        self.assertEqual(audit.final_response_status, "no_data")
        self.assertEqual(audit.fallback_reason, "supported_without_data")
        self.assertEqual(audit.pipeline_trace_json["reason_no_data"], "supported_without_data")
        self.assertEqual(
            audit.pipeline_trace_json["tool_trace"][0]["reason_no_data"],
            "filter_without_match",
        )

    def test_group_c_combined_active_productivity_executes_analytics_without_clarification(self):
        self.client.login(username=self.user.username, password=self.password)

        model_response_without_tool = SimpleNamespace(
            id="resp_1",
            output_text="Resposta sem function call.",
            output=[],
        )
        mock_client = Mock()
        mock_client.responses.create.side_effect = [model_response_without_tool]
        recorded_args = []

        def _tool_side_effect(name, args, user=None):
            recorded_args.append((name, dict(args)))
            return {
                "date_from": "2026-03-01",
                "date_to": "2026-03-30",
                "period_label": "01/03/2026 ate 30/03/2026",
                "metric": "productivity",
                "group_by": "agent",
                "ranking_order": "best",
                "only_active": True,
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                ],
                "summary": {"total_agents_considered": 1},
                "reason_no_data": None,
            }

        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            response = self._post_chat("Quais os agentes ativos e produtivos?")

        self.assertEqual(response.status_code, 200)
        self.assertIn("mais produtivo", response.json()["answer"])
        self.assertEqual(mock_client.responses.create.call_count, 1)
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        productivity_args = next(args for name, args in recorded_args if name == "get_productivity_analytics")
        self.assertEqual(productivity_args.get("only_active"), True)

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.final_response_status, "completed")
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_productivity_analytics")
        self.assertEqual(audit.pipeline_trace_json["final_answer_type"], "backend_deterministic")

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 30))
    def test_non_persistent_chat_does_not_inherit_stale_temporal_context(self, _mocked_today):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_1",
                    arguments='{"date_from":"2024-06-01","date_to":"2024-06-27","year":2024,"month":6,"period_key":"this_month"}',
                )
            ],
        )
        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response]
        recorded_args = []

        def _tool_side_effect(name, args, user=None):
            recorded_args.append((name, dict(args)))
            return {
                "date_from": "2026-03-30",
                "date_to": "2026-03-30",
                "period_label": "30/03/2026",
                "metric": "productivity",
                "group_by": "agent",
                "ranking_order": "best",
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                ],
                "summary": {"total_agents_considered": 1},
                "reason_no_data": None,
            }

        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            result = run_chat(
                user=self.user,
                text="Quais os agentes produtivos?",
                conversation_id=None,
                origin=AssistantConversationOrigin.WIDGET,
                history_messages=[],
                assistant_context={
                    "productivity_analytics": {
                        "start_date": "2024-06-01",
                        "end_date": "2024-06-27",
                        "metric": "improductivity",
                        "group_by": "agent",
                        "ranking_order": "worst",
                        "limit": 10,
                    },
                    "semantic_operational": {
                        "intent": "agent_listing_query",
                        "subject": "agent",
                        "metric": None,
                        "ranking_order": None,
                        "limit": 50,
                        "date_from": None,
                        "date_to": None,
                        "year": None,
                        "month": None,
                        "period_key": None,
                    },
                },
                persist_history=False,
            )

        self.assertEqual(result.get("final_response_status"), "completed")
        productivity_args = next(args for name, args in recorded_args if name == "get_productivity_analytics")
        self.assertNotIn("date_from", productivity_args)
        self.assertNotIn("date_to", productivity_args)
        self.assertNotIn("year", productivity_args)
        self.assertNotIn("month", productivity_args)
        self.assertNotIn("period_key", productivity_args)
        self.assertEqual(productivity_args.get("metric"), "productivity")
        self.assertEqual(productivity_args.get("group_by"), "agent")
        self.assertEqual(productivity_args.get("ranking_order"), "best")

    def test_group_e_backend_executes_required_tool_even_without_function_call(self):
        response_without_tool = SimpleNamespace(
            id="resp_1",
            output_text="Os agentes produtivos sao Alice e Bruno.",
            output=[],
        )

        with self._mock_openai_client_with_responses([response_without_tool]), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date_from": "2026-03-01",
                "date_to": "2026-03-30",
                "period_label": "01/03/2026 ate 30/03/2026",
                "metric": "productivity",
                "group_by": "agent",
                "ranking_order": "best",
                "dimension_available": True,
                "ranking": [
                    {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                    {"agent_name": "Bruno", "tempo_produtivo_hhmm": "06:20:00"},
                ],
                "summary": {"total_agents_considered": 2},
            },
        ):
            response = self._post_chat("Quais os agentes mais produtivos hoje?")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Top 2 de produtividade", response.json()["answer"])
        self.assertEqual(AssistantActionLog.objects.count(), 1)

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.final_response_status, "completed")
        self.assertEqual(audit.fallback_reason, "")
        self.assertNotEqual(audit.fallback_reason, "required_query_tool_not_executed")
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_productivity_analytics")

    def test_sequence_listing_then_productivity_completes_without_runtime_failure(self):
        mock_client = Mock()
        listing_response_without_tool = SimpleNamespace(
            id="resp_1",
            output_text="Resposta do modelo sem function call.",
            output=[],
        )
        productivity_function_call = SimpleNamespace(
            id="resp_2",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_prod_1",
                    arguments='{"metric":"productivity","ranking_order":"best","group_by":"agent"}',
                )
            ],
        )
        def _tool_side_effect(name, args, user=None):
            if name == "get_agents_listing":
                return {
                    "only_active": False,
                    "limit": 50,
                    "total_found": 2,
                    "items": [
                        {"agent_id": 1, "cd_operador": 1001, "agent_name": "Alice", "is_active": True},
                        {"agent_id": 2, "cd_operador": 1002, "agent_name": "Bruno", "is_active": True},
                    ],
                    "reason_no_data": None,
                }
            if name == "get_productivity_analytics":
                return {
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-30",
                    "period_label": "01/03/2026 ate 30/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "dimension_available": True,
                    "ranking": [
                        {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                        {"agent_name": "Bruno", "tempo_produtivo_hhmm": "06:20:00"},
                    ],
                    "summary": {"total_agents_considered": 2},
                    "reason_no_data": None,
                }
            return {}

        mock_client.responses.create.side_effect = [
            listing_response_without_tool,
            productivity_function_call,
        ]
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            first_response = self._post_chat("Quais agentes existem no sistema?")
            self.assertEqual(first_response.status_code, 200)
            conversation_id = first_response.json()["conversation_id"]

            second_response = self._post_chat(
                "Quais os agentes mais produtivos hoje?",
                conversation_id=conversation_id,
            )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("Top 2 de produtividade", second_response.json()["answer"])

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.capability_id, "productivity_analytics_query")
        self.assertEqual(audit.final_response_status, "completed")
        self.assertEqual(audit.fallback_reason, "")
        self.assertNotEqual(audit.final_response_status, "temporary_failure")
        self.assertEqual(audit.pipeline_trace_json["tool_args"]["limit"], 10)
        self.assertEqual(mock_client.responses.create.call_count, 2)

    def test_second_model_call_is_avoided_for_structured_productivity_response(self):
        listing_response_without_tool = SimpleNamespace(
            id="resp_1",
            output_text="Resposta do modelo sem function call.",
            output=[],
        )
        productivity_function_call = SimpleNamespace(
            id="resp_2",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_prod_1",
                    arguments="{}",
                )
            ],
        )

        def _tool_side_effect(name, args, user=None):
            if name == "get_agents_listing":
                return {
                    "only_active": False,
                    "limit": 50,
                    "total_found": 1,
                    "items": [
                        {"agent_id": 1, "cd_operador": 1001, "agent_name": "Alice", "is_active": True},
                    ],
                    "reason_no_data": None,
                }
            if name == "get_productivity_analytics":
                return {
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-30",
                    "period_label": "01/03/2026 ate 30/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "dimension_available": True,
                    "ranking": [
                        {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                    ],
                    "summary": {"total_agents_considered": 1},
                    "reason_no_data": None,
                }
            return {}

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            listing_response_without_tool,
            productivity_function_call,
            RuntimeError("forced_openai_failure_after_tool_output"),
        ]

        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            first_response = self._post_chat("Quais agentes existem no sistema?")
            conversation_id = first_response.json()["conversation_id"]
            second_response = self._post_chat(
                "Quais os agentes mais produtivos hoje?",
                conversation_id=conversation_id,
            )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("No periodo de", second_response.json()["answer"])
        self.assertIn("mais produtivo", second_response.json()["answer"])
        self.assertEqual(mock_client.responses.create.call_count, 2)

        audit = AssistantAuditLog.objects.order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.capability_id, "productivity_analytics_query")
        self.assertEqual(audit.final_response_status, "completed")
        self.assertEqual(audit.fallback_reason, "")
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_productivity_analytics")
        self.assertEqual(audit.pipeline_trace_json["tool_result_rows"], 1)
        self.assertEqual(audit.pipeline_trace_json["final_answer_type"], "backend_deterministic")

    def test_second_turn_payload_uses_output_text_for_assistant_history(self):
        responses_queue = [
            SimpleNamespace(
                id="resp_1",
                output_text="Resposta do modelo sem function call.",
                output=[],
            ),
            SimpleNamespace(
                id="resp_2",
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="get_productivity_analytics",
                        call_id="call_prod_1",
                        arguments='{"metric":"productivity","ranking_order":"best","group_by":"agent"}',
                    )
                ],
            ),
        ]

        def _responses_create_side_effect(**kwargs):
            for item in kwargs.get("input") or []:
                if item.get("role") != "assistant":
                    continue
                for chunk in item.get("content") or []:
                    if chunk.get("type") == "input_text":
                        raise AssertionError(
                            "assistant history must not be serialized as input_text"
                        )
            return responses_queue.pop(0)

        def _tool_side_effect(name, args, user=None):
            if name == "get_agents_listing":
                return {
                    "only_active": False,
                    "limit": 50,
                    "total_found": 2,
                    "items": [
                        {"agent_id": 1, "cd_operador": 1001, "agent_name": "Alice", "is_active": True},
                        {"agent_id": 2, "cd_operador": 1002, "agent_name": "Bruno", "is_active": True},
                    ],
                    "reason_no_data": None,
                }
            if name == "get_productivity_analytics":
                return {
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-30",
                    "period_label": "01/03/2026 ate 30/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "dimension_available": True,
                    "ranking": [
                        {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                        {"agent_name": "Bruno", "tempo_produtivo_hhmm": "06:20:00"},
                    ],
                    "summary": {"total_agents_considered": 2},
                    "reason_no_data": None,
                }
            return {}

        mock_client = Mock()
        mock_client.responses.create.side_effect = _responses_create_side_effect

        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            first_response = self._post_chat("Quais agentes existem no sistema?")
            conversation_id = first_response.json()["conversation_id"]
            second_response = self._post_chat(
                "Quais os agentes mais produtivos hoje?",
                conversation_id=conversation_id,
            )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("Top 2 de produtividade", second_response.json()["answer"])
        self.assertEqual(mock_client.responses.create.call_count, 2)

        second_request_payload = mock_client.responses.create.call_args_list[1].kwargs["input"]
        assistant_chunks = [
            chunk
            for item in second_request_payload
            if item.get("role") == "assistant"
            for chunk in (item.get("content") or [])
        ]
        self.assertTrue(assistant_chunks)
        self.assertTrue(all(chunk.get("type") == "output_text" for chunk in assistant_chunks))

    @patch("apps.assistant.services.semantic_resolution.timezone.localdate", return_value=date(2026, 3, 30))
    def test_today_query_does_not_keep_stale_day_from_model_function_call(self, _mocked_today):
        listing_response_without_tool = SimpleNamespace(
            id="resp_1",
            output_text="Resposta do modelo sem function call.",
            output=[],
        )
        productivity_function_call_with_stale_day = SimpleNamespace(
            id="resp_2",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_productivity_analytics",
                    call_id="call_prod_1",
                    arguments='{"date_from":"2024-06-19","date_to":"2024-06-19","metric":"productivity","ranking_order":"best","group_by":"agent"}',
                )
            ],
        )

        mock_client = Mock()
        mock_client.responses.create.side_effect = [
            listing_response_without_tool,
            productivity_function_call_with_stale_day,
        ]
        recorded_args = []

        def _tool_side_effect(name, args, user=None):
            recorded_args.append((name, dict(args)))
            if name == "get_agents_listing":
                return {
                    "only_active": False,
                    "limit": 50,
                    "total_found": 2,
                    "items": [
                        {"agent_id": 1, "cd_operador": 1001, "agent_name": "Alice", "is_active": True},
                        {"agent_id": 2, "cd_operador": 1002, "agent_name": "Bruno", "is_active": True},
                    ],
                    "reason_no_data": None,
                }
            if name == "get_productivity_analytics":
                return {
                    "date_from": "2026-03-30",
                    "date_to": "2026-03-30",
                    "period_label": "30/03/2026",
                    "metric": "productivity",
                    "group_by": "agent",
                    "ranking_order": "best",
                    "dimension_available": True,
                    "ranking": [
                        {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                    ],
                    "summary": {"total_agents_considered": 1},
                    "reason_no_data": None,
                }
            return {}

        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=_tool_side_effect,
        ):
            first_response = self._post_chat("Quais agentes existem no sistema?")
            conversation_id = first_response.json()["conversation_id"]
            second_response = self._post_chat(
                "Quais os agentes mais produtivos hoje?",
                conversation_id=conversation_id,
            )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("No periodo de 30/03/2026", second_response.json()["answer"])

        productivity_args = next(args for name, args in recorded_args if name == "get_productivity_analytics")
        self.assertEqual(productivity_args.get("period_key"), "today")
        self.assertNotIn("date_from", productivity_args)
        self.assertNotIn("date_to", productivity_args)
        self.assertEqual(productivity_args.get("limit"), 10)


class AssistantProductivityResponseBuilderInvestigationTests(SimpleTestCase):
    def test_builder_handles_valid_ranking(self):
        result = {
            "period_label": "01/03/2026 ate 30/03/2026",
            "metric": "productivity",
            "ranking_order": "best",
            "group_by": "agent",
            "summary": {"total_agents_considered": 2},
            "ranking": [
                {"agent_name": "Alice", "tempo_produtivo_hhmm": "07:00:00"},
                {"agent_name": "Bruno", "tempo_produtivo_hhmm": "06:20:00"},
            ],
        }

        text = _build_productivity_analytics_response(result)

        self.assertIsInstance(text, str)
        self.assertIn("Top 2 de produtividade", text)

    def test_builder_handles_empty_ranking_without_exception(self):
        result = {
            "period_label": "30/03/2026",
            "metric": "productivity",
            "ranking_order": "best",
            "group_by": "agent",
            "summary": {"total_agents_considered": 0},
            "ranking": [],
        }

        text = _build_productivity_analytics_response(result)

        self.assertIsNone(text)

    def test_builder_handles_partial_and_null_fields_without_exception(self):
        result = {
            "period_label": None,
            "metric": "performance",
            "ranking_order": "worst",
            "group_by": "agent",
            "summary": {"total_agents_considered": None},
            "ranking": [
                {
                    "agent_name": None,
                    "team_name": None,
                    "taxa_ocupacao_pct": None,
                    "tempo_produtivo_hhmm": None,
                    "tempo_improdutivo_hhmm": None,
                }
            ],
        }

        text = _build_productivity_analytics_response(result)

        self.assertIsInstance(text, str)
        self.assertIn("taxa de ocupacao indisponivel", text)
