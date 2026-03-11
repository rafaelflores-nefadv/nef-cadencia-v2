import re
from dataclasses import dataclass

from apps.assistant.services.assistant_config import (
    ASSISTANT_ACTION_FAILURE_RESPONSE,
    ASSISTANT_CAPABILITIES_RESPONSE,
    ASSISTANT_FALSE_ACTION_CLAIM_TERMS,
    ASSISTANT_FALSE_DATA_CLAIM_TERMS,
    ASSISTANT_NO_DATA_RESPONSE,
    ASSISTANT_QUERY_FAILURE_RESPONSE,
    ASSISTANT_SPECULATIVE_CERTAINTY_TERMS,
    ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
    ASSISTANT_UNVERIFIED_RESPONSE,
)
from apps.assistant.services.guardrails import DENTRO_DO_ESCOPO, FORA_DO_ESCOPO, normalize_user_text
from apps.assistant.services.tool_registry import (
    TOOL_GET_CURRENT_PAUSES,
    TOOL_GET_DAY_SUMMARY,
    TOOL_GET_PAUSE_RANKING,
    TOOL_GET_PRODUCTIVITY_ANALYTICS,
    TOOL_NOTIFY_SUPERVISORS,
    TOOL_SEND_MESSAGE_TO_AGENT,
)


CONSULTA_SUPORTADA = "CONSULTA_SUPORTADA"
ACAO_SUPORTADA = "ACAO_SUPORTADA"
NAO_SUPORTADA = "NAO_SUPORTADA"
SUPORTADA_MAS_SEM_DADOS = "SUPORTADA_MAS_SEM_DADOS"


@dataclass(frozen=True)
class CapabilityDefinition:
    capability_id: str
    category: str
    description: str
    patterns: tuple[str, ...]
    query_tools: tuple[str, ...] = ()
    action_tools: tuple[str, ...] = ()
    direct_response: str | None = None
    unsupported_response: str | None = None
    no_data_response: str | None = None
    query_failure_response: str | None = None
    action_failure_response: str | None = None
    unverified_response: str | None = None

    @property
    def allowed_tools(self) -> tuple[str, ...]:
        return self.query_tools + self.action_tools

    @property
    def requires_tool(self) -> bool:
        return bool(self.allowed_tools)

    @property
    def requires_model(self) -> bool:
        return self.direct_response is None


@dataclass(frozen=True)
class CapabilityAssessment:
    category: str
    capability_id: str
    description: str
    allowed_tools: tuple[str, ...] = ()
    query_tools: tuple[str, ...] = ()
    action_tools: tuple[str, ...] = ()
    direct_response: str | None = None
    unsupported_response: str | None = None
    no_data_response: str | None = None
    query_failure_response: str | None = None
    action_failure_response: str | None = None
    unverified_response: str | None = None
    reason: str = ""

    @property
    def requires_tool(self) -> bool:
        return bool(self.allowed_tools)

    @property
    def requires_model(self) -> bool:
        return self.direct_response is None


@dataclass(frozen=True)
class ToolExecutionRecord:
    name: str
    status: str
    result: dict
    has_data: bool | None = None


@dataclass(frozen=True)
class CapabilityValidationResult:
    classification: str
    response: str | None = None
    reason: str = ""


HELP_PATTERNS = (
    r"\b(o que|quais)\b.*\b(voce|eustacio)\b.*\b(pode|consegue)\b.*\b(fazer|consultar|executar)\b",
    r"\b(capacidades|capacidade|funcionalidades do eustacio)\b",
)

UNSUPPORTED_CAPABILITY_PATTERNS = (
    r"\b(sera|preveja|prever|previsao|projecao)\b.*\b(desempenho|operacao|operacional)\b",
    r"\b(mes que vem|semana que vem|amanha|futuro)\b.*\b(desempenho|operacao|produtividade)\b",
    r"\b(crie|criar|cadastre|configure|altere|edite|atualize|remova|delete|exclua)\b.*\b(regra|regras|configuracao|dashboard|relatorio|usuario)\b",
    r"\b(gere|gerar|crie)\b.*\b(novo relatorio|relatorio novo|dashboard novo)\b",
)

CAPABILITY_DEFINITIONS = (
    CapabilityDefinition(
        capability_id="capabilities_help",
        category=CONSULTA_SUPORTADA,
        description="explicar as capacidades reais do Eustacio",
        patterns=HELP_PATTERNS,
        direct_response=ASSISTANT_CAPABILITIES_RESPONSE,
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="pause_ranking_then_notify_agent",
        category=ACAO_SUPORTADA,
        description="consultar ranking de pausas e enviar mensagem para o agente identificado",
        patterns=(
            r"\b(envie|mande)\b.*\b(mensagem|alerta)\b.*\b(agente)\b.*\b(mais pausas|maior pausa|estourou pausa)\b",
        ),
        query_tools=(TOOL_GET_PAUSE_RANKING,),
        action_tools=(TOOL_SEND_MESSAGE_TO_AGENT,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="current_pauses_query",
        category=CONSULTA_SUPORTADA,
        description="consultar quem esta em pausa agora",
        patterns=(
            r"\b(quem|quais|quantos|liste|listar|mostre|mostrar)\b.*\bem pausa\b.*\b(agora|atualmente|neste momento)\b",
            r"\b(em pausa agora|em pausa neste momento|em pausa atualmente|estao em pausa agora)\b",
        ),
        query_tools=(TOOL_GET_CURRENT_PAUSES,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="pause_ranking_query",
        category=CONSULTA_SUPORTADA,
        description="consultar ranking de pausas por data",
        patterns=(
            r"\b(ranking|top|quem)\b.*\b(pausa|pausas|estourou pausa|mais pausas|maior pausa|overflow)\b",
            r"\b(pausa|pausas)\b.*\b(ranking|top|excesso)\b",
        ),
        query_tools=(TOOL_GET_PAUSE_RANKING,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="day_summary_query",
        category=CONSULTA_SUPORTADA,
        description="consultar resumo operacional diario",
        patterns=(
            r"\b(resumo|sumario|totais?)\b.*\b(operacional|dia|hoje)\b",
            r"\b(operacional|dia|hoje)\b.*\b(resumo|sumario|totais?)\b",
        ),
        query_tools=(TOOL_GET_DAY_SUMMARY,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="productivity_analytics_query",
        category=CONSULTA_SUPORTADA,
        description="consultar produtividade, improdutividade ou desempenho operacional por periodo",
        patterns=(
            r"\b(qual|quais|quem|ranking|top|mostre|mostrar|liste|listar)\b.*\b"
            r"(agente|agentes|operador|operadores|equipe|equipes)\b.*\b"
            r"(produtiv[a-z]*|improdutiv[a-z]*|desempenho|performance)\b",
            r"\b(produtiv[a-z]*|improdutiv[a-z]*|desempenho|performance)\b.*\b"
            r"(agente|agentes|operador|operadores|equipe|equipes)\b",
            r"\b(agente|agentes|operador|operadores|equipe|equipes)\b.*\b"
            r"(mais improdutiv[a-z]*|menos produtiv[a-z]*|pior desempenho|melhor desempenho)\b",
            r"\b(ranking|top)\b.*\b(produtiv[a-z]*|improdutiv[a-z]*|desempenho|performance)\b",
        ),
        query_tools=(TOOL_GET_PRODUCTIVITY_ANALYTICS,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="send_message_to_agent",
        category=ACAO_SUPORTADA,
        description="enviar mensagem suportada para um agente",
        patterns=(
            r"\b(envie|mande)\b.*\b(mensagem|alerta|aviso)\b.*\b(agente)\b",
        ),
        action_tools=(TOOL_SEND_MESSAGE_TO_AGENT,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
    CapabilityDefinition(
        capability_id="notify_supervisors",
        category=ACAO_SUPORTADA,
        description="notificar supervisores com templates suportados",
        patterns=(
            r"\b(notifique|avise|envie)\b.*\b(supervisor|supervisores)\b",
        ),
        action_tools=(TOOL_NOTIFY_SUPERVISORS,),
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
    ),
)


def _build_assessment(definition: CapabilityDefinition, reason: str) -> CapabilityAssessment:
    return CapabilityAssessment(
        category=definition.category,
        capability_id=definition.capability_id,
        description=definition.description,
        allowed_tools=definition.allowed_tools,
        query_tools=definition.query_tools,
        action_tools=definition.action_tools,
        direct_response=definition.direct_response,
        unsupported_response=definition.unsupported_response or ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=definition.no_data_response or ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=definition.query_failure_response or ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=definition.action_failure_response or ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=definition.unverified_response or ASSISTANT_UNVERIFIED_RESPONSE,
        reason=reason,
    )


def assess_capability(text: str) -> CapabilityAssessment:
    normalized_text = normalize_user_text(text)
    if not normalized_text:
        return CapabilityAssessment(
            category=NAO_SUPORTADA,
            capability_id="unsupported_empty",
            description="solicitacao vazia",
            unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
            no_data_response=ASSISTANT_NO_DATA_RESPONSE,
            query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
            action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
            unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
            reason="empty_text",
        )

    if any(re.search(pattern, normalized_text) for pattern in HELP_PATTERNS):
        return _build_assessment(CAPABILITY_DEFINITIONS[0], "help_request")

    if any(re.search(pattern, normalized_text) for pattern in UNSUPPORTED_CAPABILITY_PATTERNS):
        return CapabilityAssessment(
            category=NAO_SUPORTADA,
            capability_id="unsupported_known_request",
            description="solicitacao fora da capacidade real",
            unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
            no_data_response=ASSISTANT_NO_DATA_RESPONSE,
            query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
            action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
            unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
            reason="unsupported_pattern",
        )

    for definition in CAPABILITY_DEFINITIONS[1:]:
        if any(re.search(pattern, normalized_text) for pattern in definition.patterns):
            return _build_assessment(definition, "capability_match")

    return CapabilityAssessment(
        category=NAO_SUPORTADA,
        capability_id="unsupported_unknown_request",
        description="solicitacao sem capacidade correspondente",
        unsupported_response=ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE,
        no_data_response=ASSISTANT_NO_DATA_RESPONSE,
        query_failure_response=ASSISTANT_QUERY_FAILURE_RESPONSE,
        action_failure_response=ASSISTANT_ACTION_FAILURE_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
        reason="no_capability_match",
    )


def build_capability_instruction(assessment: CapabilityAssessment) -> str:
    if not assessment.requires_tool:
        return (
            f"Capacidade validada: {assessment.description}. "
            "Responda apenas com base nas capacidades reais listadas pelo sistema. "
            "Nao invente consultas, dados, acoes ou funcionalidades inexistentes."
        )

    allowed_tools = ", ".join(assessment.allowed_tools)
    return (
        f"Capacidade validada: {assessment.description}. "
        f"Tools permitidas nesta solicitacao: {allowed_tools}. "
        "Nao afirme que consultou dados, encontrou resultados, enviou mensagens ou concluiu a acao "
        "sem tool bem-sucedida. "
        "Se nao houver dados suficientes, diga claramente que nao encontrou dados suficientes no sistema. "
        "Se a tool falhar, diga claramente que nao foi possivel concluir a consulta ou acao naquele momento. "
        "Nao improvise funcionalidades que nao existem."
    )


def build_tool_execution_record(name: str, status: str, result: dict) -> ToolExecutionRecord:
    return ToolExecutionRecord(
        name=name,
        status=status,
        result=result if isinstance(result, dict) else {},
        has_data=tool_result_has_data(name, result if isinstance(result, dict) else {}),
    )


def tool_result_has_data(tool_name: str, result: dict) -> bool | None:
    if not isinstance(result, dict):
        return None

    if tool_name == TOOL_GET_PAUSE_RANKING:
        return bool(result.get("ranking"))

    if tool_name == TOOL_GET_CURRENT_PAUSES:
        return "total_in_pause" in result and "items" in result

    if tool_name == TOOL_GET_DAY_SUMMARY:
        totals = result.get("totals") if isinstance(result.get("totals"), dict) else {}
        agents_with_stats = int(totals.get("agents_with_stats") or 0)
        return agents_with_stats > 0 or bool(result.get("top3"))

    if tool_name == TOOL_GET_PRODUCTIVITY_ANALYTICS:
        if result.get("dimension_available") is False:
            return False
        return bool(result.get("ranking"))

    return None


def evaluate_capability_runtime(
    assessment: CapabilityAssessment,
    tool_records: list[ToolExecutionRecord],
) -> CapabilityValidationResult:
    if assessment.category == NAO_SUPORTADA:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unsupported_response,
            reason=assessment.reason or "unsupported_capability",
        )

    if not assessment.requires_tool:
        return CapabilityValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="no_tool_required",
        )

    relevant_records = [record for record in tool_records if record.name in assessment.allowed_tools]
    query_records = [record for record in relevant_records if record.name in assessment.query_tools]
    action_records = [record for record in relevant_records if record.name in assessment.action_tools]

    if any(record.status == "error" for record in query_records):
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.query_failure_response,
            reason="query_tool_error",
        )

    if any(record.status == "error" for record in action_records):
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.action_failure_response,
            reason="action_tool_error",
        )

    if assessment.query_tools and not query_records:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="required_query_tool_not_executed",
        )

    successful_query_records = [record for record in query_records if record.status == "success"]
    if assessment.query_tools and not successful_query_records:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="required_query_tool_without_success",
        )

    if successful_query_records and all(record.has_data is False for record in successful_query_records):
        return CapabilityValidationResult(
            classification=SUPORTADA_MAS_SEM_DADOS,
            response=assessment.no_data_response,
            reason="supported_without_data",
        )

    if assessment.action_tools and not action_records:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="required_action_tool_not_executed",
        )

    return CapabilityValidationResult(
        classification=DENTRO_DO_ESCOPO,
        reason="capability_runtime_confirmed",
    )


def validate_operational_truthfulness(
    assessment: CapabilityAssessment,
    answer: str,
    tool_records: list[ToolExecutionRecord],
) -> CapabilityValidationResult:
    normalized_answer = normalize_user_text(answer)
    if not normalized_answer:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="empty_answer",
        )

    transparent_responses = {
        normalize_user_text(assessment.direct_response or ""),
        normalize_user_text(assessment.unsupported_response or ""),
        normalize_user_text(assessment.no_data_response or ""),
        normalize_user_text(assessment.query_failure_response or ""),
        normalize_user_text(assessment.action_failure_response or ""),
        normalize_user_text(assessment.unverified_response or ""),
    }
    if normalized_answer in transparent_responses:
        return CapabilityValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="transparent_response",
        )

    successful_query_records = [
        record for record in tool_records
        if record.name in assessment.query_tools and record.status == "success"
    ]
    successful_action_records = [
        record for record in tool_records
        if record.name in assessment.action_tools and record.status == "success"
    ]

    if any(term in normalized_answer for term in ASSISTANT_FALSE_ACTION_CLAIM_TERMS):
        if not successful_action_records:
            return CapabilityValidationResult(
                classification=FORA_DO_ESCOPO,
                response=assessment.unverified_response,
                reason="false_action_claim",
            )

    if any(term in normalized_answer for term in ASSISTANT_FALSE_DATA_CLAIM_TERMS):
        if not successful_query_records:
            return CapabilityValidationResult(
                classification=FORA_DO_ESCOPO,
                response=assessment.unverified_response,
                reason="false_data_claim",
            )

    if any(term in normalized_answer for term in ASSISTANT_SPECULATIVE_CERTAINTY_TERMS):
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="speculative_certainty",
        )

    if assessment.query_tools and not successful_query_records:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="query_answer_without_verified_tool",
        )

    if assessment.action_tools and not tool_records:
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response,
            reason="action_answer_without_attempt",
        )

    return CapabilityValidationResult(
        classification=DENTRO_DO_ESCOPO,
        reason="operational_truth_validated",
    )
