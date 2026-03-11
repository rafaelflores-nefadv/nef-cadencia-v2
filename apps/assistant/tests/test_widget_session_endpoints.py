import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from apps.assistant.models import AssistantAuditLog, AssistantConversation, AssistantMessage
from apps.assistant.services.assistant_config import (
    ASSISTANT_CAPABILITIES_RESPONSE,
    ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
)


User = get_user_model()


class AssistantWidgetSessionEndpointsTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.user = User.objects.create_user(username="widget_user", password=self.password)
        self.factory = RequestFactory()
        self.widget_chat_url = reverse("assistant-widget-chat")
        self.widget_end_url = reverse("assistant-widget-end-session")
        self.widget_save_url = reverse("assistant-widget-save-session")
        self.session_a = "widget_session_a1"
        self.session_b = "widget_session_b2"

    def _widget_chat(self, session_id, text):
        return self.client.post(
            self.widget_chat_url,
            data=json.dumps(
                {
                    "text": text,
                    "widget_session_id": session_id,
                }
            ),
            content_type="application/json",
        )

    def _widget_save(self, session_id):
        return self.client.post(
            self.widget_save_url,
            data=json.dumps({"widget_session_id": session_id}),
            content_type="application/json",
        )

    def _widget_end(self, session_id):
        return self.client.post(
            self.widget_end_url,
            data=json.dumps({"widget_session_id": session_id}),
            content_type="application/json",
        )

    def test_widget_chat_does_not_persist_history_automatically(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], ASSISTANT_CAPABILITIES_RESPONSE)
        self.assertIsNone(payload["conversation_id"])
        self.assertEqual(AssistantConversation.objects.count(), 0)
        self.assertEqual(AssistantMessage.objects.count(), 0)

    def test_widget_chat_still_creates_audit_log_without_persisted_conversation(self):
        self.client.login(username=self.user.username, password=self.password)

        self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")

        self.assertEqual(AssistantAuditLog.objects.count(), 1)
        audit = AssistantAuditLog.objects.first()
        self.assertIsNone(audit.conversation)
        self.assertEqual(audit.origin, "widget")
        self.assertEqual(audit.scope_classification, "DENTRO_DO_ESCOPO")
        self.assertEqual(audit.capability_id, "capabilities_help")

    def test_widget_chat_reuses_same_temporary_thread_across_multiple_messages(self):
        recorded_calls = []

        def run_chat_side_effect(**kwargs):
            recorded_calls.append(
                {
                    "text": kwargs["text"],
                    "history_messages": list(kwargs.get("history_messages") or []),
                    "assistant_context": dict(kwargs.get("assistant_context") or {}),
                }
            )
            return {
                "answer": f"Resposta para: {kwargs['text']}",
                "assistant_context": {"last_text": kwargs["text"]},
            }

        self.client.login(username=self.user.username, password=self.password)
        with patch("apps.assistant.views.run_chat", side_effect=run_chat_side_effect):
            first = self._widget_chat(self.session_a, "Primeira pergunta")
            second = self._widget_chat(self.session_a, "Segunda pergunta")
            third = self._widget_chat(self.session_a, "Terceira pergunta")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 200)
        self.assertEqual(recorded_calls[0]["history_messages"], [])
        self.assertEqual(
            recorded_calls[1]["history_messages"],
            [
                {"role": "user", "content": "Primeira pergunta"},
                {"role": "assistant", "content": "Resposta para: Primeira pergunta"},
            ],
        )
        self.assertEqual(recorded_calls[1]["assistant_context"], {"last_text": "Primeira pergunta"})
        self.assertEqual(
            recorded_calls[2]["history_messages"],
            [
                {"role": "user", "content": "Primeira pergunta"},
                {"role": "assistant", "content": "Resposta para: Primeira pergunta"},
                {"role": "user", "content": "Segunda pergunta"},
                {"role": "assistant", "content": "Resposta para: Segunda pergunta"},
            ],
        )
        self.assertEqual(recorded_calls[2]["assistant_context"], {"last_text": "Segunda pergunta"})
        self.assertEqual(third.json()["widget_session_id"], self.session_a)
        self.assertEqual(len(third.json()["messages"]), 6)

    def test_widget_save_persists_full_multi_turn_thread(self):
        self.client.login(username=self.user.username, password=self.password)

        valid_question = "O que voce consegue fazer no sistema?"
        self._widget_chat(self.session_a, valid_question)
        self._widget_chat(self.session_a, valid_question)
        self._widget_chat(self.session_a, valid_question)
        save_response = self._widget_save(self.session_a)

        self.assertEqual(save_response.status_code, 200)
        conversation = AssistantConversation.objects.get(pk=save_response.json()["conversation_id"])
        self.assertEqual(
            list(conversation.messages.values_list("content", flat=True)),
            [
                valid_question,
                ASSISTANT_CAPABILITIES_RESPONSE,
                valid_question,
                ASSISTANT_CAPABILITIES_RESPONSE,
                valid_question,
                ASSISTANT_CAPABILITIES_RESPONSE,
            ],
        )

    def test_widget_save_persists_current_temporary_session(self):
        self.client.login(username=self.user.username, password=self.password)
        self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")

        response = self._widget_save(self.session_a)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["already_saved"])
        conversation = AssistantConversation.objects.get(pk=payload["conversation_id"])
        self.assertEqual(conversation.created_by, self.user)
        self.assertEqual(conversation.origin, "widget")
        self.assertTrue(conversation.is_persistent)
        self.assertEqual(conversation.title, "O que voce consegue fazer no sistema?")
        self.assertEqual(conversation.messages.count(), 2)

    def test_widget_save_does_not_duplicate_already_saved_conversation(self):
        self.client.login(username=self.user.username, password=self.password)
        self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")

        first_response = self._widget_save(self.session_a)
        second_response = self._widget_save(self.session_a)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(AssistantConversation.objects.count(), 1)
        self.assertEqual(
            first_response.json()["conversation_id"],
            second_response.json()["conversation_id"],
        )
        self.assertTrue(second_response.json()["already_saved"])

    def test_widget_close_ends_session_and_save_fails_for_closed_session(self):
        self.client.login(username=self.user.username, password=self.password)
        self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")

        end_response = self._widget_end(self.session_a)
        save_response = self._widget_save(self.session_a)

        self.assertEqual(end_response.status_code, 200)
        self.assertTrue(end_response.json()["ended"])
        self.assertEqual(save_response.status_code, 400)
        self.assertEqual(save_response.json()["detail"], "Nao ha mensagens para salvar nesta sessao.")
        self.assertEqual(AssistantConversation.objects.count(), 0)

    def test_widget_reopen_starts_new_clean_session(self):
        self.client.login(username=self.user.username, password=self.password)
        self._widget_chat(self.session_a, "O que voce consegue fazer no sistema?")
        self._widget_end(self.session_a)

        second_chat_response = self._widget_chat(self.session_b, "Crie uma nova regra operacional")
        save_response = self._widget_save(self.session_b)

        self.assertEqual(second_chat_response.status_code, 200)
        self.assertEqual(second_chat_response.json()["answer"], ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE)
        self.assertEqual(save_response.status_code, 200)

        conversation = AssistantConversation.objects.get(pk=save_response.json()["conversation_id"])
        message_contents = list(conversation.messages.values_list("content", flat=True))
        self.assertEqual(
            message_contents,
            [
                "Crie uma nova regra operacional",
                ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
            ],
        )

    def test_widget_template_includes_processing_status_component(self):
        request = self.factory.get("/")
        request.user = self.user

        html = render_to_string("assistant/_assistant_widget.html", {"request": request})

        self.assertIn("assistant-widget-processing-config", html)
        self.assertIn("assistant-processing__text", html)
        self.assertIn('id="assistant-typing" class="assistant-widget__typing" hidden', html)
        self.assertIn("Entendendo sua pergunta", html)
        self.assertIn("Salvar conversa", html)
