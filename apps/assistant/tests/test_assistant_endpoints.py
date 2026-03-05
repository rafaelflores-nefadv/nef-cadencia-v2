import json
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.assistant.models import AssistantConversation
from apps.assistant.services.assistant_service import (
    ASSISTANT_CONFIG_ERROR_RESPONSE,
    ASSISTANT_DISABLED_RESPONSE,
)
from apps.rules.models import SystemConfig, SystemConfigValueType


User = get_user_model()


class AssistantEndpointsTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="user1", password=self.password)
        self.other_user = User.objects.create_user(username="user2", password=self.password)
        self.chat_url = reverse("assistant-chat")

    def _mock_openai_client(self, answer: str):
        mock_client = Mock()
        mock_client.responses.create.return_value = SimpleNamespace(output_text=answer)
        return patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        )

    def test_logged_user_creates_conversation_with_post_chat(self):
        self.client.login(username=self.user.username, password=self.password)

        with self._mock_openai_client("Resposta real do assistente"):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Oi, assistente"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("conversation_id", payload)
        self.assertEqual(payload["answer"], "Resposta real do assistente")

        conversation = AssistantConversation.objects.get(id=payload["conversation_id"])
        self.assertEqual(conversation.created_by, self.user)
        self.assertEqual(conversation.messages.count(), 2)

    def test_get_conversation_history_returns_messages(self):
        self.client.login(username=self.user.username, password=self.password)
        with self._mock_openai_client("Contexto carregado"):
            create_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Primeira mensagem"}),
                content_type="application/json",
            )
        conversation_id = create_response.json()["conversation_id"]

        response = self.client.get(reverse("assistant-conversation", args=[conversation_id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["conversation_id"], conversation_id)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertEqual(payload["messages"][1]["role"], "assistant")
        self.assertEqual(payload["messages"][1]["content"], "Contexto carregado")
        self.assertIn("created_at", payload["messages"][0])

    def test_different_user_cannot_access_foreign_conversation(self):
        self.client.login(username=self.user.username, password=self.password)
        with self._mock_openai_client("Mensagem privada de retorno"):
            create_response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Mensagem privada"}),
                content_type="application/json",
            )
        conversation_id = create_response.json()["conversation_id"]
        self.client.logout()

        self.client.login(username=self.other_user.username, password=self.password)
        response = self.client.get(reverse("assistant-conversation", args=[conversation_id]))

        self.assertEqual(response.status_code, 404)

    def test_chat_returns_disabled_answer_when_openai_disabled(self):
        SystemConfig.objects.create(
            config_key="OPENAI_ENABLED",
            config_value="false",
            value_type=SystemConfigValueType.BOOL,
        )
        self.client.login(username=self.user.username, password=self.password)

        with patch("apps.assistant.services.assistant_service.get_openai_client") as mocked_client:
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Teste com assistente desativado"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("desativado", payload["answer"].lower())
        self.assertEqual(payload["answer"], ASSISTANT_DISABLED_RESPONSE)
        mocked_client.assert_not_called()
        conversation = AssistantConversation.objects.get(id=payload["conversation_id"])
        self.assertEqual(conversation.messages.count(), 2)

    def test_chat_returns_friendly_answer_when_api_key_is_missing(self):
        self.client.login(username=self.user.username, password=self.password)

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": "Teste sem chave"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_CONFIG_ERROR_RESPONSE)
        self.assertIn("OPENAI_API_KEY", payload["answer"])
        conversation = AssistantConversation.objects.get(id=payload["conversation_id"])
        self.assertEqual(conversation.messages.count(), 2)
