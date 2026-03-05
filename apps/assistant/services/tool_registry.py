from apps.assistant.services.tools_actions import notify_supervisors, send_message_to_agent
from apps.assistant.services.tools_read import (
    get_current_pauses,
    get_day_summary,
    get_pause_ranking,
)

TOOL_GET_PAUSE_RANKING = "get_pause_ranking"
TOOL_GET_CURRENT_PAUSES = "get_current_pauses"
TOOL_GET_DAY_SUMMARY = "get_day_summary"
TOOL_SEND_MESSAGE_TO_AGENT = "send_message_to_agent"
TOOL_NOTIFY_SUPERVISORS = "notify_supervisors"


def get_tools_schema() -> list[dict]:
    return [
        {
            "type": "function",
            "name": TOOL_GET_PAUSE_RANKING,
            "description": (
                "Retorna ranking de pausas por agente para uma data, incluindo total e excesso."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD. Exemplo: 2026-03-05",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Quantidade maxima de agentes no ranking.",
                        "default": 10,
                    },
                    "pause_type": {
                        "type": "string",
                        "description": "Filtro opcional por nome da pausa.",
                    },
                },
                "required": ["date"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": TOOL_GET_CURRENT_PAUSES,
            "description": "Retorna quem esta em pausa agora e totais por tipo de pausa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pause_type": {
                        "type": "string",
                        "description": "Filtro opcional por nome da pausa.",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": TOOL_GET_DAY_SUMMARY,
            "description": "Retorna resumo operacional do dia com totais e top 3 agentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD. Exemplo: 2026-03-05",
                    },
                },
                "required": ["date"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": TOOL_SEND_MESSAGE_TO_AGENT,
            "description": (
                "Envia mensagem para um agente com template permitido e canal especificado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "integer"},
                    "template_key": {"type": "string"},
                    "channel": {"type": "string"},
                    "variables": {
                        "type": "object",
                        "description": "Variaveis para renderizacao do template.",
                    },
                },
                "required": ["agent_id", "template_key", "channel"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": TOOL_NOTIFY_SUPERVISORS,
            "description": "Notifica supervisores via template permitido e canal especificado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_key": {"type": "string"},
                    "channel": {"type": "string"},
                    "variables": {
                        "type": "object",
                        "description": "Variaveis para renderizacao do template.",
                    },
                },
                "required": ["template_key", "channel"],
                "additionalProperties": False,
            },
        },
    ]


def execute_tool(name: str, args: dict, user) -> dict:
    if not getattr(user, "is_authenticated", False):
        return {"status": "denied", "reason": "Usuario nao autenticado"}

    args = args or {}
    if name == TOOL_GET_PAUSE_RANKING:
        return get_pause_ranking(
            date=args.get("date"),
            limit=args.get("limit", 10),
            pause_type=args.get("pause_type"),
        )
    if name == TOOL_GET_CURRENT_PAUSES:
        return get_current_pauses(
            pause_type=args.get("pause_type"),
        )
    if name == TOOL_GET_DAY_SUMMARY:
        return get_day_summary(
            date=args.get("date"),
        )
    if name == TOOL_SEND_MESSAGE_TO_AGENT:
        return send_message_to_agent(
            user=user,
            agent_id=args.get("agent_id"),
            template_key=args.get("template_key"),
            channel=args.get("channel"),
            variables=args.get("variables") or {},
        )
    if name == TOOL_NOTIFY_SUPERVISORS:
        return notify_supervisors(
            user=user,
            template_key=args.get("template_key"),
            channel=args.get("channel"),
            variables=args.get("variables") or {},
        )

    return {"status": "denied", "reason": f"Tool nao permitida: {name}"}
