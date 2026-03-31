import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.assistant.models import (
    AssistantActionLog,
    AssistantAuditLog,
    AssistantConversationOrigin,
    AssistantMessageRole,
)
from apps.assistant.observability import (
    AUDIT_EVENT_CHAT_MESSAGE,
    AUDIT_EVENT_CONVERSATION_DELETED,
    AUDIT_EVENT_WIDGET_SESSION_ENDED,
    AUDIT_EVENT_WIDGET_SESSION_SAVED,
    AUDIT_STATUS_BLOCKED_CAPABILITY,
    AUDIT_STATUS_BLOCKED_SCOPE,
    AUDIT_STATUS_COMPLETED,
    AUDIT_STATUS_FAIL_SAFE,
    AUDIT_STATUS_TOOL_FAILURE,
    BLOCK_REASON_OUT_OF_SCOPE_PHRASE,
    FALLBACK_REASON_QUERY_TOOL_ERROR,
    FALLBACK_REASON_RESPONSE_OUT_OF_SCOPE_PHRASE,
)
from apps.assistant.services.assistant_config import (
    ASSISTANT_CAPABILITIES_RESPONSE,
    ASSISTANT_OUT_OF_SCOPE_RESPONSE,
    ASSISTANT_QUERY_FAILURE_RESPONSE,
    ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
    ASSISTANT_UNVERIFIED_RESPONSE,
)
from apps.assistant.services.audit_service import record_assistant_audit
from apps.assistant.services.conversation_store import (
    add_message_to_conversation,
    create_persistent_conversation,
)
from apps.assistant.services.metrics_service import get_assistant_metrics


User = get_user_model()


class AssistantObservabilityTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="obs_user", password=self.password)
        self.chat_url = reverse("assistant-chat")
        self.widget_chat_url = reverse("assistant-widget-chat")
        self.widget_save_url = reverse("assistant-widget-save-session")
        self.widget_end_url = reverse("assistant-widget-end-session")
        self.page_conversations_url = reverse("assistant-page-conversations-api")
        self.widget_session_id = "widget_obs_001"

    def _login(self):
        self.client.login(username=self.user.username, password=self.password)

    def _post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_normal_flow_creates_structured_audit(self):
        self._login()

        response = self._post_json(
            self.chat_url,
            {"text": "O que voce consegue fazer no sistema?"},
        )

        self.assertEqual(response.status_code, 200)
        audit = AssistantAuditLog.objects.get()
        self.assertEqual(audit.event_type, AUDIT_EVENT_CHAT_MESSAGE)
        self.assertEqual(audit.origin, AssistantConversationOrigin.WIDGET)
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_COMPLETED)
        self.assertEqual(audit.response_text, ASSISTANT_CAPABILITIES_RESPONSE)
        self.assertIsNotNone(audit.conversation)

    def test_scope_block_creates_blocked_scope_audit(self):
        self._login()

        response = self._post_json(
            self.chat_url,
            {"text": "Qual a capital da Franca?"},
        )

        self.assertEqual(response.status_code, 200)
        audit = AssistantAuditLog.objects.get()
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_BLOCKED_SCOPE)
        self.assertEqual(audit.block_reason, BLOCK_REASON_OUT_OF_SCOPE_PHRASE)

    def test_capability_refusal_creates_blocked_capability_audit(self):
        self._login()

        response = self._post_json(
            self.chat_url,
            {"text": "Crie uma nova regra operacional"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE)
        audit = AssistantAuditLog.objects.get()
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_BLOCKED_CAPABILITY)
        self.assertEqual(audit.capability_classification, "NAO_SUPORTADA")

    def test_tool_failure_creates_tool_failure_audit(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_pause_ranking",
                    call_id="call_1",
                    arguments='{"date":"2026-03-09","limit":5}',
                )
            ],
        )
        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response]

        self._login()
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            side_effect=RuntimeError("tool exploded"),
        ):
            response = self._post_json(
                self.chat_url,
                {"text": "Quem mais estourou pausa hoje?"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], ASSISTANT_QUERY_FAILURE_RESPONSE)
        audit = AssistantAuditLog.objects.get()
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_TOOL_FAILURE)
        self.assertEqual(audit.fallback_reason, FALLBACK_REASON_QUERY_TOOL_ERROR)
        self.assertEqual(audit.tools_attempted_json, ["get_pause_ranking"])
        self.assertEqual(audit.tools_succeeded_json, [])
        self.assertEqual(AssistantActionLog.objects.get().status, "error")

    def test_output_fail_safe_creates_audit_when_model_leaves_scope(self):
        first_response = SimpleNamespace(
            id="resp_1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_day_summary",
                    call_id="call_1",
                    arguments='{"date":"2026-03-09"}',
                )
            ],
        )
        second_response = SimpleNamespace(
            id="resp_2",
            output_text="A capital da Franca e Paris.",
            output=[],
        )
        mock_client = Mock()
        mock_client.responses.create.side_effect = [first_response, second_response]

        self._login()
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ), patch(
            "apps.assistant.services.assistant_service.execute_tool",
            return_value={
                "date": "2026-03-09",
                "totals": {"agents_with_stats": 3, "active_agents": 5, "in_pause_now": 1},
                "top3": [{"agent_id": 1, "agent_name": "Alice", "total_minutes": 20}],
            },
        ):
            response = self._post_json(
                self.chat_url,
                {"text": "Mostre o resumo operacional de hoje"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], ASSISTANT_OUT_OF_SCOPE_RESPONSE)
        audit = AssistantAuditLog.objects.get()
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_FAIL_SAFE)
        self.assertEqual(
            audit.fallback_reason,
            FALLBACK_REASON_RESPONSE_OUT_OF_SCOPE_PHRASE,
        )

    def test_widget_save_and_end_create_operational_audits(self):
        self._login()
        self._post_json(
            self.widget_chat_url,
            {
                "text": "O que voce consegue fazer no sistema?",
                "widget_session_id": self.widget_session_id,
            },
        )

        save_response = self._post_json(
            self.widget_save_url,
            {"widget_session_id": self.widget_session_id},
        )
        end_response = self._post_json(
            self.widget_end_url,
            {"widget_session_id": self.widget_session_id},
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(end_response.status_code, 200)

        save_audit = AssistantAuditLog.objects.filter(
            event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED
        ).get()
        end_audit = AssistantAuditLog.objects.filter(
            event_type=AUDIT_EVENT_WIDGET_SESSION_ENDED
        ).get()

        self.assertEqual(save_audit.final_response_status, AUDIT_STATUS_COMPLETED)
        self.assertEqual(save_audit.origin, AssistantConversationOrigin.WIDGET)
        self.assertIsNotNone(save_audit.conversation)
        self.assertEqual(end_audit.final_response_status, AUDIT_STATUS_COMPLETED)
        self.assertEqual(end_audit.origin, AssistantConversationOrigin.WIDGET)

    def test_delete_conversation_creates_operational_audit(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        self._login()

        response = self._post_json(
            reverse("assistant-page-delete-conversation", args=[conversation.id]),
            {},
        )

        self.assertEqual(response.status_code, 200)
        audit = AssistantAuditLog.objects.get(event_type=AUDIT_EVENT_CONVERSATION_DELETED)
        self.assertEqual(audit.final_response_status, AUDIT_STATUS_COMPLETED)
        self.assertEqual(audit.conversation, conversation)

    def test_metrics_service_returns_consolidated_values(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.USER,
            content="Quais agentes estao em pausa agora?",
        )
        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.ASSISTANT,
            content="Sou o Eustacio, assistente da plataforma.",
        )
        AssistantActionLog.objects.create(
            conversation=conversation,
            requested_by=self.user,
            tool_name="get_pause_ranking",
            tool_args_json={"date": "2026-03-09"},
            status="error",
            result_text="tool exploded",
        )

        record_assistant_audit(
            user=self.user,
            conversation=conversation,
            origin=AssistantConversationOrigin.WIDGET,
            input_text="O que voce consegue fazer no sistema?",
            final_response_status=AUDIT_STATUS_COMPLETED,
            response_text=ASSISTANT_CAPABILITIES_RESPONSE,
        )
        record_assistant_audit(
            user=self.user,
            origin=AssistantConversationOrigin.WIDGET,
            input_text="Qual a capital da Franca?",
            block_reason=BLOCK_REASON_OUT_OF_SCOPE_PHRASE,
            final_response_status=AUDIT_STATUS_BLOCKED_SCOPE,
            response_text=ASSISTANT_UNVERIFIED_RESPONSE,
        )
        record_assistant_audit(
            user=self.user,
            conversation=conversation,
            origin=AssistantConversationOrigin.PAGE,
            input_text="Crie uma nova regra operacional",
            capability_classification="NAO_SUPORTADA",
            final_response_status=AUDIT_STATUS_BLOCKED_CAPABILITY,
            response_text=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        )
        record_assistant_audit(
            user=self.user,
            conversation=conversation,
            origin=AssistantConversationOrigin.PAGE,
            input_text="Quem mais estourou pausa hoje?",
            fallback_reason=FALLBACK_REASON_QUERY_TOOL_ERROR,
            final_response_status=AUDIT_STATUS_TOOL_FAILURE,
            response_text=ASSISTANT_QUERY_FAILURE_RESPONSE,
        )
        record_assistant_audit(
            user=self.user,
            origin=AssistantConversationOrigin.WIDGET,
            input_text="Mostre o resumo operacional de hoje",
            fallback_reason=FALLBACK_REASON_RESPONSE_OUT_OF_SCOPE_PHRASE,
            final_response_status=AUDIT_STATUS_FAIL_SAFE,
            response_text=ASSISTANT_UNVERIFIED_RESPONSE,
        )
        record_assistant_audit(
            user=self.user,
            conversation=conversation,
            origin=AssistantConversationOrigin.WIDGET,
            event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED,
            input_text="Salvar conversa do widget",
            final_response_status=AUDIT_STATUS_COMPLETED,
            response_text="Conversa do widget salva com sucesso.",
        )

        metrics = get_assistant_metrics(user=self.user)

        self.assertEqual(metrics["messages_total"], 2)
        self.assertEqual(metrics["saved_conversations_total"], 1)
        self.assertEqual(metrics["interactions_by_origin"]["widget"], 4)
        self.assertEqual(metrics["interactions_by_origin"]["page"], 2)
        self.assertEqual(metrics["blocked_scope_total"], 1)
        self.assertEqual(metrics["blocked_capability_total"], 1)
        self.assertEqual(metrics["tool_failures_total"], 1)
        self.assertEqual(metrics["fallbacks_total"], 2)
        self.assertEqual(metrics["successful_responses_total"], 1)
        self.assertEqual(metrics["events_by_type"][AUDIT_EVENT_WIDGET_SESSION_SAVED], 1)
