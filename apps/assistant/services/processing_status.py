from dataclasses import dataclass, field


PROCESSING_STATUS_UNDERSTANDING_QUERY = "understanding_query"
PROCESSING_STATUS_CHECKING_CONTEXT = "checking_context"
PROCESSING_STATUS_RESOLVING_INTENT = "resolving_intent"
PROCESSING_STATUS_QUERYING_DATABASE = "querying_database"
PROCESSING_STATUS_RUNNING_TOOL = "running_tool"
PROCESSING_STATUS_FILTERING_RESULTS = "filtering_results"
PROCESSING_STATUS_BUILDING_RESPONSE = "building_response"
PROCESSING_STATUS_VALIDATING_RESPONSE = "validating_response"
PROCESSING_STATUS_COMPLETED = "completed"
PROCESSING_STATUS_FAILED = "failed"


PROCESSING_STATUS_LABELS = {
    PROCESSING_STATUS_UNDERSTANDING_QUERY: "Entendendo sua pergunta",
    PROCESSING_STATUS_CHECKING_CONTEXT: "Verificando o contexto da conversa",
    PROCESSING_STATUS_RESOLVING_INTENT: "Interpretando sua solicitacao",
    PROCESSING_STATUS_QUERYING_DATABASE: "Consultando dados no sistema",
    PROCESSING_STATUS_RUNNING_TOOL: "Buscando informacoes",
    PROCESSING_STATUS_FILTERING_RESULTS: "Filtrando os dados para melhor resultado",
    PROCESSING_STATUS_BUILDING_RESPONSE: "Montando a resposta",
    PROCESSING_STATUS_VALIDATING_RESPONSE: "Validando a resposta final",
    PROCESSING_STATUS_COMPLETED: "Resposta concluida",
    PROCESSING_STATUS_FAILED: "Nao foi possivel concluir o processamento",
}

PROCESSING_STATUS_FALLBACK_SEQUENCES = {
    "default": [
        PROCESSING_STATUS_UNDERSTANDING_QUERY,
        PROCESSING_STATUS_CHECKING_CONTEXT,
        PROCESSING_STATUS_RESOLVING_INTENT,
        PROCESSING_STATUS_BUILDING_RESPONSE,
        PROCESSING_STATUS_VALIDATING_RESPONSE,
    ],
    "analytics": [
        PROCESSING_STATUS_UNDERSTANDING_QUERY,
        PROCESSING_STATUS_CHECKING_CONTEXT,
        PROCESSING_STATUS_RESOLVING_INTENT,
        PROCESSING_STATUS_QUERYING_DATABASE,
        PROCESSING_STATUS_FILTERING_RESULTS,
        PROCESSING_STATUS_BUILDING_RESPONSE,
        PROCESSING_STATUS_VALIDATING_RESPONSE,
    ],
    "tool": [
        PROCESSING_STATUS_UNDERSTANDING_QUERY,
        PROCESSING_STATUS_CHECKING_CONTEXT,
        PROCESSING_STATUS_RESOLVING_INTENT,
        PROCESSING_STATUS_RUNNING_TOOL,
        PROCESSING_STATUS_BUILDING_RESPONSE,
        PROCESSING_STATUS_VALIDATING_RESPONSE,
    ],
    "blocked": [
        PROCESSING_STATUS_UNDERSTANDING_QUERY,
        PROCESSING_STATUS_RESOLVING_INTENT,
        PROCESSING_STATUS_VALIDATING_RESPONSE,
    ],
}


def get_processing_label(status: str) -> str:
    return PROCESSING_STATUS_LABELS.get(status, "Pensando...")


def build_processing_ui_config() -> dict:
    return {
        "labels": PROCESSING_STATUS_LABELS,
        "fallbackSequences": PROCESSING_STATUS_FALLBACK_SEQUENCES,
    }


@dataclass
class ProcessingStatusTrace:
    items: list[str] = field(default_factory=list)

    def emit(self, status: str) -> None:
        if not status:
            return
        if self.items and self.items[-1] == status:
            return
        self.items.append(status)

    def emit_many(self, *statuses: str) -> None:
        for status in statuses:
            self.emit(status)

    def finalize_completed(self) -> None:
        self.emit(PROCESSING_STATUS_COMPLETED)

    def finalize_failed(self) -> None:
        self.emit(PROCESSING_STATUS_FAILED)

    def serialize(self) -> list[dict]:
        return [
            {"status": status, "label": get_processing_label(status)}
            for status in self.items
        ]
