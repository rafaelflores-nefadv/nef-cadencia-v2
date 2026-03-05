import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.assistant.models import AssistantActionLog
from apps.integrations.models import Integration
from apps.messaging.models import MessageTemplate
from apps.monitoring.models import Agent, AgentDayStats, NotificationHistory
from apps.rules.models import SystemConfig, SystemConfigValueType


User = get_user_model()


class AssistantToolsActionsTests(TestCase):
    def setUp(self):
        self.password = "test-pass-123"
        self.staff_user = User.objects.create_user(
            username="staff_user",
            password=self.password,
            is_staff=True,
            email="staff@example.com",
        )
        self.normal_user = User.objects.create_user(
            username="normal_user",
            password=self.password,
            email="normal@example.com",
        )
        self.other_staff = User.objects.create_user(
            username="other_staff",
            password=self.password,
            is_staff=True,
            email="other_staff@example.com",
        )
        self.agent = Agent.objects.create(cd_operador=2001, nm_agente="Agente A", email="agent@example.com")
        self.chat_url = reverse("assistant-chat")

        Integration.objects.create(
            name="ChatSeguro Stub",
            channel="chatseguro",
            enabled=True,
            config_json={},
        )
        MessageTemplate.objects.create(
            name="pause_overflow",
            template_type="muitas_pausas",
            channel="chatseguro",
            body="Agente {{ agent_name }} excedeu {{ overflow_minutes }} minutos.",
            active=True,
        )
        MessageTemplate.objects.create(
            name="supervisor_alert",
            template_type="supervisor_alerta",
            channel="chatseguro",
            body="Alerta: {{ total_in_pause }} agentes em pausa.",
            active=True,
        )

    def _response_with_tool_call(self, name: str, arguments: dict, response_id: str):
        return SimpleNamespace(
            id=response_id,
            output=[
                SimpleNamespace(
                    type="function_call",
                    name=name,
                    call_id=f"call_{response_id}",
                    arguments=json.dumps(arguments),
                )
            ],
        )

    def _response_with_text(self, text: str, response_id: str):
        return SimpleNamespace(id=response_id, output_text=text, output=[])

    def _post_with_mocked_model(self, user, model_responses, text="execute"):
        mock_client = Mock()
        mock_client.responses.create.side_effect = model_responses
        self.client.login(username=user.username, password=self.password)
        with patch(
            "apps.assistant.services.assistant_service.get_openai_client",
            return_value=mock_client,
        ):
            response = self.client.post(
                self.chat_url,
                data=json.dumps({"text": text}),
                content_type="application/json",
            )
        self.client.logout()
        return response

    def test_non_staff_user_gets_denied_for_send_message_action(self):
        response = self._post_with_mocked_model(
            user=self.normal_user,
            model_responses=[
                self._response_with_tool_call(
                    "send_message_to_agent",
                    {
                        "agent_id": self.agent.id,
                        "template_key": "pause_overflow",
                        "channel": "chatseguro",
                        "variables": {"agent_name": "Agente A", "overflow_minutes": 12},
                    },
                    response_id="1",
                ),
                self._response_with_text("Acao negada por permissao.", response_id="2"),
            ],
            text="Envie mensagem para o agente A",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(NotificationHistory.objects.count(), 0)
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        log = AssistantActionLog.objects.first()
        self.assertEqual(log.status, "denied")
        self.assertEqual(log.tool_name, "send_message_to_agent")

    def test_staff_user_success_creates_action_log_and_notification_history(self):
        response = self._post_with_mocked_model(
            user=self.staff_user,
            model_responses=[
                self._response_with_tool_call(
                    "send_message_to_agent",
                    {
                        "agent_id": self.agent.id,
                        "template_key": "pause_overflow",
                        "channel": "chatseguro",
                        "variables": {"agent_name": "Agente A", "overflow_minutes": 15},
                    },
                    response_id="1",
                ),
                self._response_with_text("Mensagem enviada com sucesso.", response_id="2"),
            ],
            text="Envie mensagem para o agente A",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(NotificationHistory.objects.count(), 1)
        history = NotificationHistory.objects.first()
        self.assertEqual(history.status, "SENT")
        self.assertEqual(AssistantActionLog.objects.count(), 1)
        log = AssistantActionLog.objects.first()
        self.assertEqual(log.status, "success")
        self.assertEqual(log.tool_name, "send_message_to_agent")

    def test_throttle_skips_second_send_within_window(self):
        payload = {
            "agent_id": self.agent.id,
            "template_key": "pause_overflow",
            "channel": "chatseguro",
            "variables": {"agent_name": "Agente A", "overflow_minutes": 8},
        }
        self._post_with_mocked_model(
            user=self.staff_user,
            model_responses=[
                self._response_with_tool_call("send_message_to_agent", payload, response_id="1"),
                self._response_with_text("Primeiro envio.", response_id="2"),
            ],
            text="Primeiro envio",
        )
        self._post_with_mocked_model(
            user=self.staff_user,
            model_responses=[
                self._response_with_tool_call("send_message_to_agent", payload, response_id="3"),
                self._response_with_text("Segundo envio throttled.", response_id="4"),
            ],
            text="Segundo envio",
        )

        self.assertEqual(NotificationHistory.objects.count(), 2)
        statuses = list(NotificationHistory.objects.order_by("id").values_list("status", flat=True))
        self.assertEqual(statuses[0], "SENT")
        self.assertEqual(statuses[1], "SKIPPED")

        self.assertEqual(AssistantActionLog.objects.count(), 2)
        latest_log = AssistantActionLog.objects.order_by("-id").first()
        self.assertEqual(latest_log.status, "denied")
        self.assertEqual(latest_log.tool_name, "send_message_to_agent")

    def test_template_not_allowed_returns_denied(self):
        SystemConfig.objects.create(
            config_key="ASSISTANT_ALLOWED_TEMPLATES_JSON",
            config_value='["supervisor_alert"]',
            value_type=SystemConfigValueType.JSON,
        )
        response = self._post_with_mocked_model(
            user=self.staff_user,
            model_responses=[
                self._response_with_tool_call(
                    "send_message_to_agent",
                    {
                        "agent_id": self.agent.id,
                        "template_key": "pause_overflow",
                        "channel": "chatseguro",
                        "variables": {"agent_name": "Agente A", "overflow_minutes": 7},
                    },
                    response_id="1",
                ),
                self._response_with_text("Template bloqueado.", response_id="2"),
            ],
            text="Envie alerta",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(NotificationHistory.objects.count(), 0)
        log = AssistantActionLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "denied")

    def test_chat_can_chain_read_then_action_tools(self):
        AgentDayStats.objects.create(
            agent=self.agent,
            cd_operador=self.agent.cd_operador,
            data_ref=timezone.localdate(),
            qtd_pausas=3,
            tempo_pausas_seg=40 * 60,
        )

        response = self._post_with_mocked_model(
            user=self.staff_user,
            model_responses=[
                self._response_with_tool_call(
                    "get_pause_ranking",
                    {"date": timezone.localdate().isoformat(), "limit": 1},
                    response_id="1",
                ),
                self._response_with_tool_call(
                    "send_message_to_agent",
                    {
                        "agent_id": self.agent.id,
                        "template_key": "pause_overflow",
                        "channel": "chatseguro",
                        "variables": {"agent_name": "Agente A", "overflow_minutes": 20},
                    },
                    response_id="2",
                ),
                self._response_with_text("Ranking consultado e mensagem enviada.", response_id="3"),
            ],
            text="envie mensagem pro agente que mais estourou pausa hoje",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AssistantActionLog.objects.count(), 2)
        tool_names = list(AssistantActionLog.objects.order_by("id").values_list("tool_name", flat=True))
        self.assertEqual(tool_names, ["get_pause_ranking", "send_message_to_agent"])
        self.assertEqual(NotificationHistory.objects.count(), 1)
