from django.test import SimpleTestCase

from apps.assistant.services.assistant_config import (
    ASSISTANT_CAPABILITIES_RESPONSE,
    ASSISTANT_NO_DATA_RESPONSE,
    ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
    ASSISTANT_UNVERIFIED_RESPONSE,
)
from apps.assistant.services.capabilities import (
    CONSULTA_SUPORTADA,
    NAO_SUPORTADA,
    SUPORTADA_MAS_SEM_DADOS,
    ToolExecutionRecord,
    assess_capability,
    evaluate_capability_runtime,
    validate_operational_truthfulness,
)
from apps.assistant.services.tool_registry import (
    TOOL_GET_CURRENT_PAUSES,
    TOOL_GET_PAUSE_RANKING,
    TOOL_GET_PRODUCTIVITY_ANALYTICS,
)


class AssistantCapabilitiesTests(SimpleTestCase):
    def test_assess_capability_returns_supported_query_for_current_pauses(self):
        assessment = assess_capability("Quais agentes estao em pausa agora?")

        self.assertEqual(assessment.category, CONSULTA_SUPORTADA)
        self.assertEqual(assessment.allowed_tools, (TOOL_GET_CURRENT_PAUSES,))

    def test_assess_capability_returns_help_direct_response(self):
        assessment = assess_capability("O que voce consegue fazer no sistema?")

        self.assertEqual(assessment.category, CONSULTA_SUPORTADA)
        self.assertEqual(assessment.direct_response, ASSISTANT_CAPABILITIES_RESPONSE)

    def test_assess_capability_returns_unsupported_for_future_prediction(self):
        assessment = assess_capability("Me diga qual sera o desempenho da operacao mes que vem")

        self.assertEqual(assessment.category, NAO_SUPORTADA)
        self.assertEqual(assessment.unsupported_response, ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE)

    def test_assess_capability_returns_supported_query_for_productivity_analytics(self):
        assessment = assess_capability("qual o agente mais improdutivo de janeiro de 2026?")

        self.assertEqual(assessment.category, CONSULTA_SUPORTADA)
        self.assertEqual(assessment.allowed_tools, (TOOL_GET_PRODUCTIVITY_ANALYTICS,))

    def test_evaluate_capability_runtime_detects_supported_but_without_data(self):
        assessment = assess_capability("Quem mais estourou pausa hoje?")
        tool_records = [
            ToolExecutionRecord(
                name=TOOL_GET_PAUSE_RANKING,
                status="success",
                result={"date": "2026-03-09", "ranking": []},
                has_data=False,
            )
        ]

        validation = evaluate_capability_runtime(assessment, tool_records)

        self.assertEqual(validation.classification, SUPORTADA_MAS_SEM_DADOS)
        self.assertEqual(validation.response, ASSISTANT_NO_DATA_RESPONSE)

    def test_operational_truthfulness_blocks_false_action_claim_without_tool_success(self):
        assessment = assess_capability("Envie mensagem para o agente A")

        validation = validate_operational_truthfulness(
            assessment,
            "Ja enviei a mensagem para o agente.",
            [],
        )

        self.assertEqual(validation.response, ASSISTANT_UNVERIFIED_RESPONSE)
