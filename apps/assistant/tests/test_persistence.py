from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assistant.models import (
    AssistantAuditLog,
    AssistantAuditEventType,
    AssistantAuditLogStatus,
    AssistantConversationOrigin,
    AssistantConversationStatus,
    AssistantMessageRole,
    AssistantUserPreference,
)
from apps.assistant.services.audit_service import record_assistant_audit
from apps.assistant.services.assistant_config import ASSISTANT_DEFAULT_CONVERSATION_TITLE
from apps.assistant.services.conversation_store import (
    AssistantConversationLimitError,
    add_message_to_conversation,
    create_persistent_conversation,
    delete_conversation,
    generate_conversation_title,
    list_user_conversations,
)


User = get_user_model()


class AssistantPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="persist_user", password="test-pass-123")
        self.other_user = User.objects.create_user(
            username="persist_other",
            password="test-pass-123",
        )

    def test_create_persistent_conversation_uses_default_metadata(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )

        self.assertEqual(conversation.created_by, self.user)
        self.assertEqual(conversation.origin, AssistantConversationOrigin.PAGE)
        self.assertEqual(conversation.status, AssistantConversationStatus.ACTIVE)
        self.assertTrue(conversation.is_persistent)
        self.assertEqual(conversation.title, ASSISTANT_DEFAULT_CONVERSATION_TITLE)

    def test_add_message_updates_title_from_first_useful_user_message(self):
        conversation = create_persistent_conversation(self.user)

        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.USER,
            content="Oi",
        )
        conversation.refresh_from_db()
        self.assertEqual(conversation.title, ASSISTANT_DEFAULT_CONVERSATION_TITLE)

        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.USER,
            content="Quais agentes estao em pausa agora no dashboard?",
        )
        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "Quais agentes estao em pausa agora no dashboard?",
        )
        self.assertEqual(conversation.messages.count(), 2)

    def test_list_user_conversations_is_isolated_per_user(self):
        own_conversation = create_persistent_conversation(self.user)
        create_persistent_conversation(self.other_user)

        listed_ids = list(list_user_conversations(self.user).values_list("id", flat=True))

        self.assertEqual(listed_ids, [own_conversation.id])

    def test_delete_conversation_marks_deleted_and_removes_from_listing(self):
        conversation = create_persistent_conversation(self.user)

        delete_conversation(conversation, self.user)
        conversation.refresh_from_db()

        self.assertEqual(conversation.status, AssistantConversationStatus.DELETED)
        self.assertEqual(list(list_user_conversations(self.user)), [])

    def test_conversation_limit_raises_without_auto_deleting_old_records(self):
        AssistantUserPreference.objects.create(user=self.user, max_saved_conversations=1)
        first_conversation = create_persistent_conversation(self.user)

        with self.assertRaises(AssistantConversationLimitError):
            create_persistent_conversation(self.user)

        self.assertEqual(first_conversation.status, AssistantConversationStatus.ACTIVE)
        self.assertEqual(list_user_conversations(self.user).count(), 1)

    def test_generate_conversation_title_uses_fallback_and_truncates(self):
        self.assertEqual(
            generate_conversation_title("teste"),
            ASSISTANT_DEFAULT_CONVERSATION_TITLE,
        )
        self.assertTrue(
            generate_conversation_title(
                "Quais agentes estao em pausa agora no dashboard operacional da plataforma com filtros por fila e supervisor hoje?"
            ).endswith("...")
        )

    def test_record_assistant_audit_creates_operational_log(self):
        conversation = create_persistent_conversation(self.user)

        audit = record_assistant_audit(
            user=self.user,
            conversation=conversation,
            origin=AssistantConversationOrigin.WIDGET,
            input_text="Quais agentes estao em pausa agora?",
            scope_classification="DENTRO_DO_ESCOPO",
            capability_classification="CONSULTA_SUPORTADA",
            capability_id="current_pauses_query",
            tools_attempted=["get_current_pauses"],
            tools_succeeded=["get_current_pauses"],
            final_response_status=AssistantAuditLogStatus.COMPLETED,
            response_text="Resumo operacional pronto.",
            semantic_resolution={
                "intent": "current_pauses_query",
                "semantic_applied": True,
            },
            pipeline_trace={
                "question": "Quais agentes estao em pausa agora?",
                "resolved_intent": "current_pauses_query",
                "tool_selected": "get_current_pauses",
                "tool_args": {"pause_type": ""},
                "tool_result_rows": 3,
                "tool_result_preview": {"keys": ["items"]},
                "reason_no_data": "",
                "final_answer_type": "backend_deterministic",
            },
        )

        self.assertEqual(AssistantAuditLog.objects.count(), 1)
        self.assertEqual(audit.user, self.user)
        self.assertEqual(audit.conversation, conversation)
        self.assertEqual(audit.tools_attempted_json, ["get_current_pauses"])
        self.assertEqual(audit.tools_succeeded_json, ["get_current_pauses"])
        self.assertEqual(audit.event_type, AssistantAuditEventType.CHAT_MESSAGE)
        self.assertEqual(audit.final_response_status, AssistantAuditLogStatus.COMPLETED)
        self.assertEqual(audit.semantic_resolution_json["intent"], "current_pauses_query")
        self.assertEqual(audit.pipeline_trace_json["tool_selected"], "get_current_pauses")
