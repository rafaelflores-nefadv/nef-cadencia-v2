import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.assistant.models import (
    AssistantConversation,
    AssistantConversationOrigin,
    AssistantConversationStatus,
    AssistantUserPreference,
)
from apps.assistant.services.assistant_config import (
    ASSISTANT_CAPABILITIES_RESPONSE,
    ASSISTANT_DEFAULT_CONVERSATION_TITLE,
    ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
    build_conversation_limit_response,
)
from apps.assistant.services.conversation_store import (
    add_message_to_conversation,
    create_persistent_conversation,
)
from apps.assistant.models import AssistantMessageRole


User = get_user_model()


class AssistantPageTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="page_user", password=self.password)
        self.other_user = User.objects.create_user(username="page_other", password=self.password)
        self.page_url = reverse("assistant-page")
        self.conversations_api_url = reverse("assistant-page-conversations-api")
        self.chat_url = reverse("assistant-chat")

    def _create_conversation_with_messages(self, user, title_text):
        conversation = create_persistent_conversation(
            user,
            origin=AssistantConversationOrigin.PAGE,
        )
        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.USER,
            content=title_text,
        )
        add_message_to_conversation(
            conversation,
            role=AssistantMessageRole.ASSISTANT,
            content="Sou o Eustacio, assistente da plataforma.",
        )
        conversation.refresh_from_db()
        return conversation

    def test_assistant_page_lists_only_logged_user_conversations(self):
        own_conversation = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time A",
        )
        self._create_conversation_with_messages(
            self.other_user,
            "Resumo operacional do time B",
        )

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.page_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_conversation.title)
        self.assertNotContains(response, "Resumo operacional do time B")
        self.assertContains(response, "assistant-page-typing")
        self.assertContains(response, 'id="assistant-page-typing" class="assistant-page__typing" hidden')
        self.assertContains(response, "Entendendo sua pergunta")
        self.assertContains(response, '"processingUi"')
        self.assertContains(response, "assistant/assistant_message_rendering.js")

    def test_assistant_page_preselects_latest_conversation_when_history_exists(self):
        first_conversation = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time A",
        )
        latest_conversation = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time B",
        )

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.page_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_conversation"]["id"], latest_conversation.id)
        self.assertNotEqual(response.context["selected_conversation"]["id"], first_conversation.id)
        self.assertContains(response, "assistant-page-delete")
        self.assertContains(response, latest_conversation.title)

    def test_assistant_page_renders_selected_conversation_messages_in_html(self):
        conversation = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional detalhado",
        )

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(f"{self.page_url}?conversation_id={conversation.id}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumo operacional detalhado")
        self.assertContains(response, "Sou o Eustacio, assistente da plataforma.")

    def test_assistant_page_renders_empty_selected_conversation_state(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(f"{self.page_url}?conversation_id={conversation.id}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conversa iniciada")
        self.assertContains(response, "Envie a primeira pergunta")

    def test_assistant_page_new_conversation_persisted(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.conversations_api_url,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        conversation = AssistantConversation.objects.get(pk=payload["conversation"]["id"])
        self.assertEqual(conversation.created_by, self.user)
        self.assertEqual(conversation.origin, AssistantConversationOrigin.PAGE)
        self.assertEqual(conversation.title, ASSISTANT_DEFAULT_CONVERSATION_TITLE)
        self.assertTrue(conversation.is_persistent)

    def test_assistant_page_can_load_existing_conversation(self):
        conversation = self._create_conversation_with_messages(
            self.user,
            "Quais agentes estao em pausa agora?",
        )
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(
            reverse("assistant-page-conversation-api", args=[conversation.id])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["conversation"]["id"], conversation.id)
        self.assertEqual(len(payload["conversation"]["messages"]), 2)
        self.assertEqual(payload["conversation"]["messages"][0]["role"], "user")

    def test_assistant_page_can_switch_between_conversations(self):
        first = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time azul",
        )
        second = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time verde",
        )
        self.client.login(username=self.user.username, password=self.password)

        first_response = self.client.get(
            reverse("assistant-page-conversation-api", args=[first.id])
        )
        second_response = self.client.get(
            reverse("assistant-page-conversation-api", args=[second.id])
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["conversation"]["title"], first.title)
        self.assertEqual(second_response.json()["conversation"]["title"], second.title)

    def test_assistant_page_can_delete_conversation(self):
        conversation = self._create_conversation_with_messages(
            self.user,
            "Resumo operacional do time vermelho",
        )
        self.client.login(username=self.user.username, password=self.password)

        delete_response = self.client.post(
            reverse("assistant-page-delete-conversation", args=[conversation.id]),
            data=json.dumps({}),
            content_type="application/json",
        )
        list_response = self.client.get(self.conversations_api_url)

        self.assertEqual(delete_response.status_code, 200)
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, AssistantConversationStatus.DELETED)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["conversations"], [])

    def test_assistant_page_respects_conversation_limit(self):
        AssistantUserPreference.objects.create(user=self.user, max_saved_conversations=1)
        create_persistent_conversation(self.user, origin=AssistantConversationOrigin.PAGE)
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.conversations_api_url,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], build_conversation_limit_response(1))

    def test_assistant_page_send_message_uses_persistent_flow(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.chat_url,
            data=json.dumps(
                {
                    "text": "O que voce consegue fazer no sistema?",
                    "conversation_id": conversation.id,
                    "origin": "page",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_CAPABILITIES_RESPONSE)
        self.assertEqual(payload["conversation"]["origin"], "page")

        conversation.refresh_from_db()
        self.assertEqual(conversation.title, "O que voce consegue fazer no sistema?")
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(len(payload["conversation"]["messages"]), 2)

    def test_assistant_page_keeps_multiple_messages_in_same_conversation(self):
        conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        self.client.login(username=self.user.username, password=self.password)

        first_response = self.client.post(
            self.chat_url,
            data=json.dumps(
                {
                    "text": "O que voce consegue fazer no sistema?",
                    "conversation_id": conversation.id,
                    "origin": "page",
                }
            ),
            content_type="application/json",
        )
        second_response = self.client.post(
            self.chat_url,
            data=json.dumps(
                {
                    "text": "Crie uma nova regra operacional",
                    "conversation_id": conversation.id,
                    "origin": "page",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        conversation.refresh_from_db()
        self.assertEqual(conversation.messages.count(), 4)
        self.assertEqual(
            list(conversation.messages.values_list("content", flat=True)),
            [
                "O que voce consegue fazer no sistema?",
                ASSISTANT_CAPABILITIES_RESPONSE,
                "Crie uma nova regra operacional",
                ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
            ],
        )
        self.assertEqual(len(second_response.json()["conversation"]["messages"]), 4)

    def test_assistant_page_separate_conversations_do_not_mix_threads(self):
        first_conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        second_conversation = create_persistent_conversation(
            self.user,
            origin=AssistantConversationOrigin.PAGE,
        )
        self.client.login(username=self.user.username, password=self.password)

        self.client.post(
            self.chat_url,
            data=json.dumps(
                {
                    "text": "O que voce consegue fazer no sistema?",
                    "conversation_id": first_conversation.id,
                    "origin": "page",
                }
            ),
            content_type="application/json",
        )
        self.client.post(
            self.chat_url,
            data=json.dumps(
                {
                    "text": "Crie uma nova regra operacional",
                    "conversation_id": second_conversation.id,
                    "origin": "page",
                }
            ),
            content_type="application/json",
        )

        first_detail = self.client.get(
            reverse("assistant-page-conversation-api", args=[first_conversation.id])
        )
        second_detail = self.client.get(
            reverse("assistant-page-conversation-api", args=[second_conversation.id])
        )

        self.assertEqual(len(first_detail.json()["conversation"]["messages"]), 2)
        self.assertEqual(len(second_detail.json()["conversation"]["messages"]), 2)
        self.assertEqual(
            first_detail.json()["conversation"]["messages"][0]["content"],
            "O que voce consegue fazer no sistema?",
        )
        self.assertEqual(
            second_detail.json()["conversation"]["messages"][0]["content"],
            "Crie uma nova regra operacional",
        )

    def test_assistant_page_does_not_allow_loading_foreign_conversation(self):
        foreign_conversation = self._create_conversation_with_messages(
            self.other_user,
            "Resumo operacional privado",
        )
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(
            reverse("assistant-page-conversation-api", args=[foreign_conversation.id])
        )

        self.assertEqual(response.status_code, 404)
