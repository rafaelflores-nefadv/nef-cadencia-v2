import json
import logging

from apps.assistant.models import (
    AssistantActionLog,
    AssistantActionLogStatus,
    AssistantConversation,
    AssistantMessage,
    AssistantMessageRole,
)
from apps.assistant.services.openai_client import OpenAIConfigError, get_openai_client
from apps.assistant.services.openai_settings import get_openai_settings
from apps.assistant.services.tool_registry import execute_tool, get_tools_schema

logger = logging.getLogger("assistant")

SYSTEM_PROMPT = (
    "Voce e o Assistente Operacional do sistema. "
    "Responda de forma objetiva. Se nao tiver dados, peca para o usuario especificar. "
    "Para enviar mensagens use apenas as tools de acao com template_key permitido. "
    "Nao gere texto livre para acao. "
    "Se a acao for sensivel, peca confirmacao do usuario antes de chamar a tool."
)
HISTORY_CONTEXT_LIMIT = 10
MAX_TOOL_CALLS_PER_REQUEST = 3
ASSISTANT_DISABLED_RESPONSE = "Assistente desativado nas configuracoes."
ASSISTANT_CONFIG_ERROR_RESPONSE = (
    "Falha de configuracao do assistente: OPENAI_API_KEY nao definido."
)
ASSISTANT_TEMPORARY_FAILURE_RESPONSE = (
    "Falha ao contatar o assistente agora. Tente novamente."
)


def _as_dict(value):
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            return {}
    return {}


def _resolve_conversation(user, raw_conversation_id):
    try:
        conversation_id = int(raw_conversation_id)
    except (TypeError, ValueError):
        conversation_id = None

    if conversation_id is not None:
        conversation = AssistantConversation.objects.filter(pk=conversation_id).first()
        if conversation is not None and (user.is_staff or conversation.created_by_id == user.id):
            return conversation

    return AssistantConversation.objects.create(created_by=user)


def _build_responses_input(conversation: AssistantConversation) -> list[dict]:
    recent_messages = list(
        conversation.messages
        .order_by("-created_at", "-id")[:HISTORY_CONTEXT_LIMIT]
    )
    recent_messages.reverse()

    context = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
        }
    ]
    for item in recent_messages:
        context.append(
            {
                "role": item.role,
                "content": [{"type": "input_text", "text": item.content}],
            }
        )
    return context


def _extract_response_text(response) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    if isinstance(output_text, list):
        chunks = [part.strip() for part in output_text if isinstance(part, str) and part.strip()]
        if chunks:
            return "\n".join(chunks)

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""

    chunks = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            item_dict = _as_dict(item)
            content = item_dict.get("content")
        if not isinstance(content, list):
            continue
        for content_item in content:
            text = getattr(content_item, "text", None)
            if text is None and isinstance(content_item, dict):
                text = content_item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())

    return "\n".join(chunks).strip()


def _extract_tool_calls(response) -> list[dict]:
    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return []

    tool_calls = []
    for item in output:
        item_dict = _as_dict(item)
        item_type = getattr(item, "type", None) or item_dict.get("type")
        if item_type != "function_call":
            continue

        name = getattr(item, "name", None) or item_dict.get("name")
        call_id = getattr(item, "call_id", None) or item_dict.get("call_id")
        arguments = getattr(item, "arguments", None) or item_dict.get("arguments")

        if not name or not call_id:
            continue

        parsed_args = {}
        if isinstance(arguments, dict):
            parsed_args = arguments
        elif isinstance(arguments, str):
            try:
                loaded = json.loads(arguments)
                if isinstance(loaded, dict):
                    parsed_args = loaded
            except json.JSONDecodeError:
                parsed_args = {"_raw_arguments": arguments}

        tool_calls.append(
            {
                "name": name,
                "call_id": call_id,
                "arguments": parsed_args,
            }
        )
    return tool_calls


def _save_assistant_message(conversation: AssistantConversation, answer: str):
    AssistantMessage.objects.create(
        conversation=conversation,
        role=AssistantMessageRole.ASSISTANT,
        content=answer,
    )


def _log_tool_action(conversation, user, tool_name, tool_args, status, result):
    result_json = result if isinstance(result, (dict, list)) else None
    result_text = ""
    if result_json is None and result is not None:
        result_text = str(result)[:4000]

    AssistantActionLog.objects.create(
        conversation=conversation,
        requested_by=user,
        tool_name=tool_name,
        tool_args_json=tool_args or {},
        status=status,
        result_json=result_json,
        result_text=result_text,
    )


def _execute_tool_with_audit(conversation, user, call: dict) -> tuple[dict, str]:
    tool_name = call["name"]
    tool_args = call["arguments"]
    try:
        result = execute_tool(tool_name, tool_args, user=user)
        status = AssistantActionLogStatus.SUCCESS
        if isinstance(result, dict):
            result_status = (result.get("status") or "").strip().lower()
            if result_status in {"denied", "skipped"}:
                status = AssistantActionLogStatus.DENIED
            elif result_status == "error":
                status = AssistantActionLogStatus.ERROR
            elif result.get("error") == "denied":
                status = AssistantActionLogStatus.DENIED
        _log_tool_action(conversation, user, tool_name, tool_args, status, result)
        return result, status
    except Exception as exc:
        logger.exception("Falha ao executar tool de leitura: %s", tool_name)
        result = {"error": "tool_execution_error", "detail": str(exc)}
        _log_tool_action(
            conversation,
            user,
            tool_name,
            tool_args,
            AssistantActionLogStatus.ERROR,
            result,
        )
        return result, AssistantActionLogStatus.ERROR


def _call_model(client, settings, input_payload, tools_schema, previous_response_id=None):
    kwargs = {
        "model": settings["model"],
        "temperature": settings["temperature"],
        "max_output_tokens": settings["max_output_tokens"],
        "input": input_payload,
        "tools": tools_schema,
    }
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id
    return client.responses.create(**kwargs)


def run_chat(user, text: str, conversation_id: int | None):
    settings = get_openai_settings()
    conversation = _resolve_conversation(user, conversation_id)

    AssistantMessage.objects.create(
        conversation=conversation,
        role=AssistantMessageRole.USER,
        content=text,
    )

    if not settings["enabled"]:
        answer = ASSISTANT_DISABLED_RESPONSE
        _save_assistant_message(conversation, answer)
        return {"conversation_id": conversation.id, "answer": answer}

    try:
        client = get_openai_client()
        tools_schema = get_tools_schema()
        response = _call_model(
            client=client,
            settings=settings,
            input_payload=_build_responses_input(conversation),
            tools_schema=tools_schema,
        )

        executed_calls = 0
        while executed_calls < MAX_TOOL_CALLS_PER_REQUEST:
            tool_calls = _extract_tool_calls(response)
            if not tool_calls:
                break

            tool_outputs = []
            for call in tool_calls:
                if executed_calls >= MAX_TOOL_CALLS_PER_REQUEST:
                    break

                result, _ = _execute_tool_with_audit(conversation, user, call)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call["call_id"],
                        "output": json.dumps(result, ensure_ascii=False),
                    }
                )
                executed_calls += 1

            if not tool_outputs:
                break

            response = _call_model(
                client=client,
                settings=settings,
                input_payload=tool_outputs,
                tools_schema=tools_schema,
                previous_response_id=getattr(response, "id", None),
            )

        answer = _extract_response_text(response)
        if not answer:
            answer = ASSISTANT_TEMPORARY_FAILURE_RESPONSE
    except OpenAIConfigError:
        logger.warning("Falha de configuracao do assistente: OPENAI_API_KEY ausente.")
        answer = ASSISTANT_CONFIG_ERROR_RESPONSE
    except Exception:
        logger.exception("Falha ao chamar OpenAI Responses API.")
        answer = ASSISTANT_TEMPORARY_FAILURE_RESPONSE

    _save_assistant_message(conversation, answer)
    return {"conversation_id": conversation.id, "answer": answer}
