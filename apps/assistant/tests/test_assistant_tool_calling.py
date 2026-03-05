import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.assistant.models import AssistantActionLog


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
            output_text="Ranking operacional concluido.",
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
        self.assertEqual(payload["answer"], "Ranking operacional concluido.")
        mocked_execute_tool.assert_called_once()
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        log = AssistantActionLog.objects.first()
        self.assertEqual(log.tool_name, "get_pause_ranking")
        self.assertEqual(log.status, "success")
