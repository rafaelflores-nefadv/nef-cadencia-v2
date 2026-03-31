import json
import logging
import time
from copy import deepcopy
from dataclasses import replace

from django.conf import settings
from django.utils import timezone

from apps.assistant.models import (
    AssistantActionLog,
    AssistantActionLogStatus,
    AssistantConversation,
    AssistantConversationOrigin,
    AssistantMessage,
    AssistantMessageRole,
)
from apps.assistant.observability import (
    AUDIT_EVENT_CHAT_MESSAGE,
    AUDIT_STATUS_BLOCKED_CAPABILITY,
    AUDIT_STATUS_BLOCKED_LIMIT,
    AUDIT_STATUS_BLOCKED_SCOPE,
    AUDIT_STATUS_COMPLETED,
    AUDIT_STATUS_CONFIG_ERROR,
    AUDIT_STATUS_DISABLED,
    AUDIT_STATUS_FAIL_SAFE,
    AUDIT_STATUS_NO_DATA,
    AUDIT_STATUS_TEMPORARY_FAILURE,
    AUDIT_STATUS_TOOL_FAILURE,
    BLOCK_REASON_CONVERSATION_LIMIT_REACHED,
    FALLBACK_REASON_ASSISTANT_RUNTIME_ERROR,
    FALLBACK_REASON_EMPTY_MODEL_OUTPUT,
    FALLBACK_REASON_OPENAI_CONFIG_ERROR,
    FALLBACK_REASON_OPENAI_RUNTIME_ERROR,
    FALLBACK_REASON_TOOL_OUTSIDE_VALIDATED_CAPABILITY,
    TOOL_FAILURE_REASONS,
)
from apps.assistant.services.assistant_config import (
    ASSISTANT_CONFIG_ERROR_RESPONSE,
    ASSISTANT_DISABLED_RESPONSE,
    ASSISTANT_OUT_OF_SCOPE_RESPONSE,
    ASSISTANT_TEMPORARY_FAILURE_RESPONSE,
    ASSISTANT_UNVERIFIED_RESPONSE,
    build_conversation_limit_response,
)
from apps.assistant.services.capabilities import (
    CONSULTA_SUPORTADA,
    NAO_SUPORTADA,
    SUPORTADA_MAS_SEM_DADOS,
    CapabilityAssessment,
    CapabilityValidationResult,
    assess_capability,
    build_capability_instruction,
    build_tool_execution_record,
    evaluate_capability_runtime,
    validate_operational_truthfulness,
)
from apps.assistant.services.guardrails import (
    DENTRO_DO_ESCOPO,
    FORA_DO_ESCOPO,
    ScopeValidationResult,
    blocked_result,
    validate_assistant_response,
    validate_scope,
)
from apps.assistant.services.analytics_context import (
    apply_productivity_context_to_tool_args,
    build_productivity_context,
    format_productivity_context_instruction,
    get_productivity_context,
    merge_productivity_context,
)
from apps.assistant.services.semantic_resolution import (
    apply_semantic_resolution_to_tool_args,
    format_semantic_resolution_instruction,
    get_semantic_context,
    merge_semantic_context,
    resolve_semantic_operational_query,
)
from apps.assistant.services.audit_service import record_assistant_audit
from apps.assistant.services.openai_client import OpenAIConfigError, get_openai_client
from apps.assistant.services.openai_settings import get_openai_settings
from apps.assistant.services.processing_status import (
    PROCESSING_STATUS_BUILDING_RESPONSE,
    PROCESSING_STATUS_CHECKING_CONTEXT,
    PROCESSING_STATUS_COMPLETED,
    PROCESSING_STATUS_FAILED,
    PROCESSING_STATUS_FILTERING_RESULTS,
    PROCESSING_STATUS_QUERYING_DATABASE,
    PROCESSING_STATUS_RESOLVING_INTENT,
    PROCESSING_STATUS_RUNNING_TOOL,
    PROCESSING_STATUS_UNDERSTANDING_QUERY,
    PROCESSING_STATUS_VALIDATING_RESPONSE,
    ProcessingStatusTrace,
)
from apps.assistant.services.assistant_runtime_settings import (
    is_capability_guardrail_enabled,
    is_output_scope_guardrail_enabled,
    is_output_truthfulness_guardrail_enabled,
    is_scope_guardrail_enabled,
)
from apps.assistant.services.system_prompt import SYSTEM_PROMPT
from apps.assistant.services.tool_registry import (
    TOOL_GET_AGENTS_LISTING,
    TOOL_GET_PRODUCTIVITY_ANALYTICS,
    execute_tool,
    get_tools_schema,
)
from apps.assistant.services.conversation_store import (
    AssistantConversationLimitError,
    add_message_to_conversation,
    resolve_user_conversation,
)

logger = logging.getLogger("assistant")

HISTORY_CONTEXT_LIMIT = 10
MAX_TOOL_CALLS_PER_REQUEST = 3
PRODUCTIVITY_ANALYTICS_CAPABILITY_ID = "productivity_analytics_query"
AGENT_LISTING_CAPABILITY_ID = "agent_listing_query"
STRUCTURED_DETERMINISTIC_CAPABILITIES = frozenset(
    {
        PRODUCTIVITY_ANALYTICS_CAPABILITY_ID,
        AGENT_LISTING_CAPABILITY_ID,
    }
)


def _truncate_for_log(value: str | None, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


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


def _build_trace_context_snapshot(assistant_context: dict) -> dict:
    return {
        "productivity_context": deepcopy(get_productivity_context(assistant_context) or {}),
        "semantic_context": deepcopy(get_semantic_context(assistant_context) or {}),
    }


def _tool_result_rows(result: dict) -> int:
    if not isinstance(result, dict):
        return 0
    for key in ("ranking", "items", "rows"):
        value = result.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def _tool_result_preview(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}

    preview = {
        "keys": sorted(result.keys())[:12],
    }
    ranking = result.get("ranking")
    if isinstance(ranking, list):
        preview["ranking_preview"] = [
            {
                "agent_name": item.get("agent_name"),
                "team_name": item.get("team_name"),
                "tempo_produtivo_hhmm": item.get("tempo_produtivo_hhmm"),
                "tempo_improdutivo_hhmm": item.get("tempo_improdutivo_hhmm"),
                "taxa_ocupacao_pct": item.get("taxa_ocupacao_pct"),
            }
            for item in ranking[:3]
            if isinstance(item, dict)
        ]
    items = result.get("items")
    if isinstance(items, list):
        preview["items_preview"] = [
            {
                "agent_name": item.get("agent_name"),
                "cd_operador": item.get("cd_operador"),
                "is_active": item.get("is_active"),
            }
            for item in items[:5]
            if isinstance(item, dict)
        ]
    summary = result.get("summary")
    if isinstance(summary, dict):
        preview["summary"] = {
            "total_agents_considered": summary.get("total_agents_considered"),
            "total_logged_seconds": summary.get("total_logged_seconds"),
            "total_productive_seconds": summary.get("total_productive_seconds"),
            "total_improductive_seconds": summary.get("total_improductive_seconds"),
            "productivity_basis_counts": summary.get("productivity_basis_counts"),
        }
    if result.get("reason_no_data"):
        preview["reason_no_data"] = result.get("reason_no_data")
    return preview


def _build_initial_pipeline_trace(question: str, assistant_context: dict) -> dict:
    return {
        "question": question,
        "resolved_intent": "",
        "resolved_context": {
            "context_before": _build_trace_context_snapshot(assistant_context),
            "semantic_resolution": {},
            "context_after": {},
        },
        "tool_selected": "",
        "tool_args": {},
        "tool_result_rows": 0,
        "tool_result_preview": {},
        "reason_no_data": "",
        "final_answer_type": "",
        "exception": "",
        "tool_trace": [],
    }


def _build_output_validation_summary(
    output_scope_guardrail_enabled: bool,
    output_truthfulness_guardrail_enabled: bool,
) -> dict:
    return {
        "scope_guardrail_enabled": bool(output_scope_guardrail_enabled),
        "truthfulness_guardrail_enabled": bool(output_truthfulness_guardrail_enabled),
        "scope_blocked": False,
        "truthfulness_blocked": False,
        "scope_reason": "",
        "truthfulness_reason": "",
    }


def _build_response_diagnostics(
    *,
    user,
    final_response_status: str,
    fallback_reason: str,
    output_validation: dict,
    capability_id: str = "",
    pipeline_trace: dict | None = None,
    tools_attempted: list[str] | None = None,
    tools_succeeded: list[str] | None = None,
) -> dict:
    if not (
        getattr(user, "is_staff", False)
        or getattr(settings, "ASSISTANT_DEBUG", False)
    ):
        return {}
    return {
        "final_response_status": final_response_status,
        "fallback_reason": fallback_reason or "",
        "capability_id": capability_id or "",
        "tool_selected": (
            str((pipeline_trace or {}).get("tool_selected") or "")
            if isinstance(pipeline_trace, dict)
            else ""
        ),
        "tool_attempted": bool(tools_attempted),
        "tool_executed": bool(tools_succeeded),
        "reason_no_data": (
            str((pipeline_trace or {}).get("reason_no_data") or "")
            if isinstance(pipeline_trace, dict)
            else ""
        ),
        "output_validation": (
            deepcopy(output_validation) if isinstance(output_validation, dict) else {}
        ),
    }


def _log_pipeline_trace(trace: dict):
    if not getattr(settings, "ASSISTANT_DEBUG", False):
        return
    logger.warning(
        "assistant.pipeline_trace %s",
        json.dumps(trace, ensure_ascii=False, default=str),
    )


def _resolve_conversation(user, raw_conversation_id, origin=None):
    return resolve_user_conversation(user, raw_conversation_id, origin=origin)


def _build_responses_api_content_for_role(
    role: str,
    text: str,
    metadata: dict | None = None,
) -> list[dict]:
    normalized_role = str(role or "").strip().lower()
    safe_text = str(text or "")
    payload = metadata if isinstance(metadata, dict) else {}

    if normalized_role == AssistantMessageRole.ASSISTANT:
        explicit_content_type = str(
            payload.get("responses_content_type")
            or payload.get("content_type")
            or ""
        ).strip().lower()
        refusal_text = str(
            payload.get("refusal")
            or payload.get("refusal_text")
            or payload.get("response_refusal")
            or ""
        ).strip()
        if explicit_content_type == "refusal" or payload.get("is_refusal") is True:
            return [
                {
                    "type": "refusal",
                    "refusal": refusal_text or safe_text or "Refusal registrada.",
                }
            ]
        return [{"type": "output_text", "text": safe_text}]

    return [{"type": "input_text", "text": safe_text}]


def _build_responses_api_message(
    role: str,
    text: str,
    metadata: dict | None = None,
) -> dict | None:
    normalized_role = str(role or "").strip().lower()
    allowed_roles = {
        AssistantMessageRole.SYSTEM,
        AssistantMessageRole.USER,
        AssistantMessageRole.ASSISTANT,
    }
    if normalized_role not in allowed_roles:
        return None
    return {
        "role": normalized_role,
        "content": _build_responses_api_content_for_role(
            normalized_role,
            text,
            metadata=metadata,
        ),
    }


def _summarize_responses_input_schema(
    payload_items: list[dict],
) -> tuple[list[str], list[str], list[str]]:
    roles: list[str] = []
    role_content_types: list[str] = []
    content_types: list[str] = []

    for item in payload_items:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        roles.append(role)
        item_content_types: list[str] = []
        content = item.get("content")
        if isinstance(content, list):
            for chunk in content:
                if not isinstance(chunk, dict):
                    continue
                chunk_type = str(chunk.get("type") or "").strip()
                if not chunk_type:
                    continue
                item_content_types.append(chunk_type)
                content_types.append(chunk_type)
        role_content_types.append(
            f"{role}:{'|'.join(item_content_types) if item_content_types else 'none'}"
        )

    return roles, role_content_types, content_types


def _build_responses_input_from_messages(
    message_items: list[dict],
    capability_instruction: str | None = None,
    context_instruction: str | None = None,
    semantic_instruction: str | None = None,
) -> list[dict]:
    context: list[dict] = []
    system_message = _build_responses_api_message(AssistantMessageRole.SYSTEM, SYSTEM_PROMPT)
    if system_message is not None:
        context.append(system_message)
    if capability_instruction:
        message = _build_responses_api_message(
            AssistantMessageRole.SYSTEM,
            capability_instruction,
        )
        if message is not None:
            context.append(message)
    if context_instruction:
        message = _build_responses_api_message(
            AssistantMessageRole.SYSTEM,
            context_instruction,
        )
        if message is not None:
            context.append(message)
    if semantic_instruction:
        message = _build_responses_api_message(
            AssistantMessageRole.SYSTEM,
            semantic_instruction,
        )
        if message is not None:
            context.append(message)
    for item in message_items[-HISTORY_CONTEXT_LIMIT:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            payload = item.get("payload")
            metadata = payload if isinstance(payload, dict) else None
        message = _build_responses_api_message(
            role,
            content,
            metadata=metadata,
        )
        if message is not None:
            context.append(message)

    roles, role_content_types, content_types = _summarize_responses_input_schema(context)
    logger.info(
        "assistant.responses_input_built items=%s history_items=%s roles=%s role_content_types=%s content_types=%s",
        len(context),
        len(message_items[-HISTORY_CONTEXT_LIMIT:]),
        ",".join(roles),
        ",".join(role_content_types),
        ",".join(content_types),
    )
    return context


def _conversation_messages_for_context(conversation: AssistantConversation) -> list[dict]:
    recent_messages = list(
        conversation.messages
        .order_by("-created_at", "-id")[:HISTORY_CONTEXT_LIMIT]
    )
    recent_messages.reverse()
    return [
        {
            "role": item.role,
            "content": item.content,
            "metadata": item.payload_json if isinstance(item.payload_json, dict) else {},
        }
        for item in recent_messages
    ]


def _sanitize_history_messages(history_messages) -> list[dict]:
    if not isinstance(history_messages, list):
        return []

    allowed_roles = {
        AssistantMessageRole.USER,
        AssistantMessageRole.ASSISTANT,
        AssistantMessageRole.SYSTEM,
    }
    sanitized = []
    for item in history_messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in allowed_roles or not content:
            continue
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            payload = item.get("payload")
            metadata = payload if isinstance(payload, dict) else None
        sanitized_item = {"role": role, "content": content}
        if isinstance(metadata, dict) and metadata:
            sanitized_item["metadata"] = metadata
        sanitized.append(sanitized_item)
    return sanitized[-HISTORY_CONTEXT_LIMIT:]


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


def _save_assistant_message(conversation: AssistantConversation, answer: str, payload: dict | None = None):
    add_message_to_conversation(
        conversation,
        role=AssistantMessageRole.ASSISTANT,
        content=answer,
        payload=payload,
    )


def _save_user_message(conversation: AssistantConversation, text: str):
    add_message_to_conversation(
        conversation,
        role=AssistantMessageRole.USER,
        content=text,
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
        logger.exception(
            "Falha ao executar tool do assistente. tool=%s conversation_id=%s user_id=%s tool_args=%s",
            tool_name,
            getattr(conversation, "id", None),
            getattr(user, "id", None),
            json.dumps(tool_args or {}, ensure_ascii=False),
        )
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


def _merge_tool_args_with_context(
    call: dict,
    assistant_context: dict,
    semantic_resolution,
    *,
    allow_period_context_inheritance: bool,
) -> tuple[dict, bool]:
    tool_name = call["name"]
    tool_args = call["arguments"] if isinstance(call.get("arguments"), dict) else {}
    tool_args = apply_semantic_resolution_to_tool_args(
        tool_name,
        tool_args,
        semantic_resolution,
        allow_period_context_inheritance=allow_period_context_inheritance,
    )
    if tool_name != "get_productivity_analytics":
        return tool_args, False
    return apply_productivity_context_to_tool_args(
        tool_args,
        assistant_context,
        allow_period_inheritance=allow_period_context_inheritance,
    )


def _sync_semantic_resolution_with_productivity_result(semantic_resolution, productivity_context):
    if semantic_resolution is None or not isinstance(productivity_context, dict):
        return semantic_resolution

    tool_args = dict(semantic_resolution.tool_args or {})
    start_date = productivity_context.get("start_date")
    end_date = productivity_context.get("end_date")
    if start_date:
        tool_args["date_from"] = start_date
    if end_date:
        tool_args["date_to"] = end_date
    if productivity_context.get("metric"):
        tool_args["metric"] = productivity_context["metric"]
    if productivity_context.get("group_by"):
        tool_args["group_by"] = productivity_context["group_by"]
    if productivity_context.get("ranking_order"):
        tool_args["ranking_order"] = productivity_context["ranking_order"]
    if productivity_context.get("limit"):
        tool_args["limit"] = productivity_context["limit"]

    return replace(
        semantic_resolution,
        tool_args=tool_args,
        metric=productivity_context.get("metric") or semantic_resolution.metric,
        subject=productivity_context.get("group_by") or semantic_resolution.subject,
        ranking_order=(
            productivity_context.get("ranking_order") or semantic_resolution.ranking_order
        ),
        limit=productivity_context.get("limit") or semantic_resolution.limit,
    )


def _filter_tools_schema(tools_schema: list[dict], allowed_tools: tuple[str, ...]) -> list[dict]:
    if not allowed_tools:
        return tools_schema
    return [
        tool_schema
        for tool_schema in tools_schema
        if tool_schema.get("name") in allowed_tools
    ]


def _scope_validation_when_guardrail_disabled() -> ScopeValidationResult:
    return ScopeValidationResult(
        classification=DENTRO_DO_ESCOPO,
        reason="scope_guardrail_disabled",
    )


def _capability_assessment_when_guardrail_disabled() -> CapabilityAssessment:
    return CapabilityAssessment(
        category=CONSULTA_SUPORTADA,
        capability_id="capability_guardrail_disabled",
        description="avaliacao de capacidade desativada por configuracao",
        unsupported_response=ASSISTANT_UNVERIFIED_RESPONSE,
        no_data_response=ASSISTANT_UNVERIFIED_RESPONSE,
        query_failure_response=ASSISTANT_UNVERIFIED_RESPONSE,
        action_failure_response=ASSISTANT_UNVERIFIED_RESPONSE,
        unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
        reason="capability_guardrail_disabled",
    )


def _safe_validate_input(text: str) -> ScopeValidationResult:
    try:
        return validate_scope(text)
    except Exception:
        logger.exception("Falha interna ao validar escopo da mensagem do usuario.")
        return blocked_result("guardrail_input_error")


def _safe_assess_capability(text: str) -> CapabilityAssessment:
    try:
        return assess_capability(text)
    except Exception:
        logger.exception("Falha interna ao avaliar a capacidade real da solicitacao.")
        return CapabilityAssessment(
            category=NAO_SUPORTADA,
            capability_id="capability_assessment_error",
            description="falha ao avaliar capacidade",
            unsupported_response=ASSISTANT_UNVERIFIED_RESPONSE,
            no_data_response=ASSISTANT_UNVERIFIED_RESPONSE,
            query_failure_response=ASSISTANT_UNVERIFIED_RESPONSE,
            action_failure_response=ASSISTANT_UNVERIFIED_RESPONSE,
            unverified_response=ASSISTANT_UNVERIFIED_RESPONSE,
            reason="capability_assessment_error",
        )


def _safe_evaluate_capability_runtime(assessment, tool_records):
    try:
        return evaluate_capability_runtime(assessment, tool_records)
    except Exception:
        logger.exception("Falha interna ao validar a execucao da capacidade.")
        return CapabilityValidationResult(
            classification=FORA_DO_ESCOPO,
            response=assessment.unverified_response or ASSISTANT_UNVERIFIED_RESPONSE,
            reason="capability_runtime_error",
        )


def _safe_validate_output(
    user_text: str,
    answer: str,
    had_tool_calls: bool,
    assessment,
    tool_records,
    *,
    output_scope_guardrail_enabled: bool,
    output_truthfulness_guardrail_enabled: bool,
) -> tuple[CapabilityValidationResult, dict]:
    output_validation_summary = _build_output_validation_summary(
        output_scope_guardrail_enabled=output_scope_guardrail_enabled,
        output_truthfulness_guardrail_enabled=output_truthfulness_guardrail_enabled,
    )
    try:
        if output_scope_guardrail_enabled:
            scope_validation = validate_assistant_response(
                user_text=user_text,
                response_text=answer,
                had_tool_calls=had_tool_calls,
            )
            if scope_validation.classification == FORA_DO_ESCOPO:
                output_validation_summary["scope_blocked"] = True
                output_validation_summary["scope_reason"] = scope_validation.reason or ""
                logger.info(
                    "assistant.output_validation.scope_blocked reason=%s had_tool_calls=%s answer_preview=%s",
                    scope_validation.reason,
                    had_tool_calls,
                    _truncate_for_log(answer),
                )
                return (
                    CapabilityValidationResult(
                        classification=scope_validation.classification,
                        response=scope_validation.response,
                        reason=scope_validation.reason,
                    ),
                    output_validation_summary,
                )
        else:
            logger.info("assistant.output_validation.scope_bypassed")

        if output_truthfulness_guardrail_enabled:
            truth_validation = validate_operational_truthfulness(
                assessment,
                answer,
                tool_records,
            )
            if truth_validation.classification == FORA_DO_ESCOPO:
                output_validation_summary["truthfulness_blocked"] = True
                output_validation_summary["truthfulness_reason"] = truth_validation.reason or ""
                logger.info(
                    "assistant.output_validation.truthfulness_blocked reason=%s capability_id=%s answer_preview=%s",
                    truth_validation.reason,
                    assessment.capability_id,
                    _truncate_for_log(answer),
                )
            return truth_validation, output_validation_summary

        logger.info("assistant.output_validation.truthfulness_bypassed")
        return (
            CapabilityValidationResult(
                classification=DENTRO_DO_ESCOPO,
                reason="output_validation_bypassed",
            ),
            output_validation_summary,
        )
    except Exception:
        logger.exception("Falha interna ao validar resposta final do assistente.")
        return (
            CapabilityValidationResult(  # type: ignore[name-defined]
                classification=FORA_DO_ESCOPO,
                response=assessment.unverified_response or ASSISTANT_UNVERIFIED_RESPONSE,
                reason="guardrail_output_error",
            ),
            output_validation_summary,
        )


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

    last_user_input = ""
    if isinstance(input_payload, list):
        for item in reversed(input_payload):
            if not isinstance(item, dict) or item.get("role") != "user":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            text_chunks = []
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("type") == "input_text":
                    text_chunks.append(str(chunk.get("text") or "").strip())
            candidate = " ".join(part for part in text_chunks if part).strip()
            if candidate:
                last_user_input = candidate
                break

    started_at = time.monotonic()
    logger.info(
        "assistant.model.call.start model=%s temperature=%s max_output_tokens=%s tools=%s input_items=%s previous_response_id=%s last_user_input=%s",
        kwargs["model"],
        kwargs["temperature"],
        kwargs["max_output_tokens"],
        len(tools_schema) if isinstance(tools_schema, list) else 0,
        len(input_payload) if isinstance(input_payload, list) else 0,
        previous_response_id or "",
        _truncate_for_log(last_user_input),
    )
    try:
        response = client.responses.create(**kwargs)
    except Exception:
        duration_ms = round((time.monotonic() - started_at) * 1000, 2)
        logger.exception(
            "assistant.model.call.error model=%s duration_ms=%s",
            kwargs["model"],
            duration_ms,
        )
        raise

    duration_ms = round((time.monotonic() - started_at) * 1000, 2)
    response_text = _extract_response_text(response)
    logger.info(
        "assistant.model.call.finish model=%s duration_ms=%s output_text_len=%s tool_calls=%s response_id=%s",
        kwargs["model"],
        duration_ms,
        len(response_text),
        len(_extract_tool_calls(response)),
        getattr(response, "id", ""),
    )
    return response


def _first_successful_tool_result(tool_records, tool_name: str) -> dict | None:
    for record in tool_records:
        if record.name == tool_name and record.status == AssistantActionLogStatus.SUCCESS:
            return record.result if isinstance(record.result, dict) else {}
    return None


def _should_finalize_after_tool(assessment, tool_records) -> bool:
    capability_id = str(getattr(assessment, "capability_id", "") or "")
    if capability_id not in STRUCTURED_DETERMINISTIC_CAPABILITIES:
        return False
    query_tools = tuple(getattr(assessment, "query_tools", ()) or ())
    if not query_tools:
        return False
    return any(
        record.status == AssistantActionLogStatus.SUCCESS and record.name in query_tools
        for record in (tool_records or [])
    )


def _runtime_tool_diagnostics(assessment, tool_records) -> dict:
    if not isinstance(tool_records, list):
        return {
            "query_attempted": "",
            "query_success": "",
            "query_has_data_flags": "",
            "query_reason_no_data": "",
        }

    query_records = [
        record
        for record in tool_records
        if record.name in getattr(assessment, "query_tools", ())
    ]
    successful_query_records = [
        record
        for record in query_records
        if record.status == AssistantActionLogStatus.SUCCESS
    ]
    has_data_flags = ",".join(
        [
            f"{record.name}:{record.has_data}"
            for record in successful_query_records
        ]
    )
    reason_no_data = ",".join(
        [
            str((record.result or {}).get("reason_no_data") or "")
            for record in successful_query_records
            if isinstance(record.result, dict)
        ]
    )
    return {
        "query_attempted": ",".join([record.name for record in query_records]),
        "query_success": ",".join([record.name for record in successful_query_records]),
        "query_has_data_flags": has_data_flags,
        "query_reason_no_data": reason_no_data,
    }


def _build_productivity_analytics_response(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None

    ranking = result.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        return None

    top_item = ranking[0]
    if not isinstance(top_item, dict):
        return None

    period_label = str(result.get("period_label") or "o periodo consultado")
    metric = str(result.get("metric") or "").strip().lower()
    ranking_order = str(result.get("ranking_order") or "").strip().lower()
    group_by = str(result.get("group_by") or "agent").strip().lower()
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    subject_label = "agente" if group_by == "agent" else "grupo"
    subject_name = str(top_item.get("agent_name") or top_item.get("team_name") or "Sem identificacao")
    total_agents = int(summary.get("total_agents_considered") or 0)
    ranking_size = len(ranking)

    if ranking_size > 1:
        if metric == "improductivity":
            header = f"Top {ranking_size} de improdutividade no periodo de {period_label}:"
            rows = [
                f"{index}. {item.get('agent_name') or item.get('team_name') or 'Sem identificacao'}"
                f" ({item.get('tempo_improdutivo_hhmm') or '00:00:00'} de tempo improdutivo)"
                for index, item in enumerate(ranking, start=1)
            ]
        elif metric == "productivity":
            header = f"Top {ranking_size} de produtividade no periodo de {period_label}:"
            rows = [
                f"{index}. {item.get('agent_name') or item.get('team_name') or 'Sem identificacao'}"
                f" ({item.get('tempo_produtivo_hhmm') or '00:00:00'} de tempo produtivo)"
                for index, item in enumerate(ranking, start=1)
            ]
        else:
            header = f"Ranking de desempenho no periodo de {period_label}:"
            rows = [
                f"{index}. {item.get('agent_name') or item.get('team_name') or 'Sem identificacao'}"
                f" (taxa de ocupacao {str(item.get('taxa_ocupacao_pct') if item.get('taxa_ocupacao_pct') is not None else 'indisponivel').replace('.', ',')}%)"
                if item.get("taxa_ocupacao_pct") is not None
                else f"{index}. {item.get('agent_name') or item.get('team_name') or 'Sem identificacao'} (taxa de ocupacao indisponivel)"
                for index, item in enumerate(ranking, start=1)
            ]
        footer = f"O ranking considerou {total_agents} agentes com dados no sistema."
        return "\n".join([header, *rows, footer])

    if metric == "improductivity":
        metric_value = str(top_item.get("tempo_improdutivo_hhmm") or "00:00:00")
        qualifier = "mais improdutivo" if ranking_order != "best" else "menos improdutivo"
        return (
            f"No periodo de {period_label}, o {subject_label} {subject_name} foi o {qualifier}, "
            f"com {metric_value} de tempo improdutivo. "
            f"O ranking considerou {total_agents} agentes com dados no sistema."
        )

    if metric == "productivity":
        metric_value = str(top_item.get("tempo_produtivo_hhmm") or "00:00:00")
        qualifier = "mais produtivo" if ranking_order != "worst" else "menos produtivo"
        return (
            f"No periodo de {period_label}, o {subject_label} {subject_name} foi o {qualifier}, "
            f"com {metric_value} de tempo produtivo. "
            f"O ranking considerou {total_agents} agentes com dados no sistema."
        )

    occupancy_pct = top_item.get("taxa_ocupacao_pct")
    occupancy_text = (
        f"{float(occupancy_pct):.2f}%".replace(".", ",")
        if occupancy_pct is not None
        else "taxa de ocupacao indisponivel"
    )
    qualifier = "melhor desempenho" if ranking_order == "best" else "pior desempenho"
    return (
        f"No periodo de {period_label}, o {subject_label} {subject_name} teve o {qualifier}, "
        f"com taxa de ocupacao de {occupancy_text}. "
        f"O ranking considerou {total_agents} agentes com dados no sistema."
    )


def _build_productivity_analytics_payload(result: dict, text: str | None = None) -> dict | None:
    if not isinstance(result, dict):
        return None

    ranking = result.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        return None

    metric = str(result.get("metric") or "").strip().lower()
    ranking_order = str(result.get("ranking_order") or "").strip().lower()
    group_by = str(result.get("group_by") or "agent").strip().lower()
    period = str(result.get("period_label") or "Periodo consultado")
    total_agents = int((result.get("summary") or {}).get("total_agents_considered") or 0)
    count = len(ranking)
    singular_subject = "agente" if group_by == "agent" else "grupo"
    plural_subject = "agentes" if group_by == "agent" else "grupos"
    subject_label = singular_subject if count == 1 else plural_subject
    improductive_adj = "improdutivo" if count == 1 else "improdutivos"
    productive_adj = "produtivo" if count == 1 else "produtivos"

    if metric == "improductivity":
        title = (
            f"Top {count} {subject_label} mais {improductive_adj}"
            if ranking_order != "best"
            else f"Top {count} {subject_label} menos {improductive_adj}"
        )
        value_label = "tempo improdutivo"
        value_key = "tempo_improdutivo_hhmm"
        value_type = "duration"
    elif metric == "productivity":
        title = (
            f"Top {count} {subject_label} mais {productive_adj}"
            if ranking_order != "worst"
            else f"Top {count} {subject_label} menos {productive_adj}"
        )
        value_label = "tempo produtivo"
        value_key = "tempo_produtivo_hhmm"
        value_type = "duration"
    else:
        title = (
            f"Top {count} {subject_label} com melhor desempenho"
            if ranking_order == "best"
            else f"Top {count} {subject_label} com pior desempenho"
        )
        value_label = "taxa de ocupacao"
        value_key = "taxa_ocupacao_pct"
        value_type = "percentage"

    items = []
    for index, item in enumerate(ranking, start=1):
        if not isinstance(item, dict):
            continue
        raw_value = item.get(value_key)
        if value_type == "percentage" and raw_value is not None:
            raw_value = f"{float(raw_value):.2f}".replace(".", ",")
        items.append(
            {
                "rank": index,
                "name": str(item.get("agent_name") or item.get("team_name") or "Sem identificacao"),
                "value": str(raw_value or ""),
                "label": value_label,
                "value_type": value_type,
            }
        )

    return {
        "type": "ranking",
        "title": title,
        "period": period,
        "total_agents": total_agents,
        "metric": metric,
        "ranking_order": ranking_order,
        "group_by": group_by,
        "items": items,
        "text": text or "",
    }


def _build_agents_listing_response(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None
    items = result.get("items")
    if not isinstance(items, list) or not items:
        return None

    only_active = result.get("only_active") is True
    total_found = int(result.get("total_found") or len(items))
    label = "agentes ativos" if only_active else "agentes cadastrados"
    lines = [
        f"{index}. {item.get('agent_name') or 'Sem nome'} (operador {item.get('cd_operador')})"
        for index, item in enumerate(items, start=1)
        if isinstance(item, dict)
    ]
    return "\n".join(
        [
            f"Encontrei {total_found} {label} no sistema.",
            *lines[:20],
        ]
    )


def _build_agents_listing_payload(result: dict, text: str | None = None) -> dict | None:
    if not isinstance(result, dict):
        return None
    items = result.get("items")
    if not isinstance(items, list) or not items:
        return None

    only_active = result.get("only_active") is True
    return {
        "type": "list",
        "title": "Agentes ativos" if only_active else "Agentes cadastrados",
        "total_found": int(result.get("total_found") or len(items)),
        "only_active": only_active,
        "items": [
            {
                "agent_id": item.get("agent_id"),
                "cd_operador": item.get("cd_operador"),
                "name": item.get("agent_name"),
                "is_active": item.get("is_active"),
            }
            for item in items[:50]
            if isinstance(item, dict)
        ],
        "text": text or "",
    }


def _build_productivity_no_data_response(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None
    period_label = str(result.get("period_label") or "").strip()
    if not period_label:
        date_from = str(result.get("date_from") or "").strip()
        date_to = str(result.get("date_to") or "").strip()
        if date_from and date_to:
            period_label = f"{date_from} ate {date_to}"
    if not period_label:
        period_label = "o periodo consultado"

    return (
        "Sou o Eustacio, assistente da plataforma. "
        f"Nao encontrei dados de produtividade para {period_label}. "
        "Posso tentar novamente se voce informar um periodo, por exemplo hoje, esta semana ou este mes."
    )


def _build_agents_listing_no_data_response(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None
    if result.get("only_active") is True:
        return (
            "Sou o Eustacio, assistente da plataforma. "
            "Nao encontrei agentes ativos com os filtros informados."
        )
    return (
        "Sou o Eustacio, assistente da plataforma. "
        "Nao encontrei agentes cadastrados com os filtros informados."
    )


def _build_required_query_tool_call(
    assessment,
    semantic_resolution,
    *,
    allow_period_context_inheritance: bool,
) -> dict | None:
    if getattr(assessment, "capability_id", "") not in {
        PRODUCTIVITY_ANALYTICS_CAPABILITY_ID,
        "agent_listing_query",
    }:
        return None

    query_tools = tuple(getattr(assessment, "query_tools", ()) or ())
    if len(query_tools) != 1:
        return None
    tool_name = query_tools[0]
    tool_args: dict = {}
    if semantic_resolution is not None:
        tool_args = apply_semantic_resolution_to_tool_args(
            tool_name,
            tool_args,
            semantic_resolution,
            allow_period_context_inheritance=allow_period_context_inheritance,
        )

    if tool_name == "get_pause_ranking" and not tool_args.get("date"):
        tool_args["date"] = timezone.localdate().isoformat()
    if tool_name == "get_day_summary" and not tool_args.get("date"):
        tool_args["date"] = timezone.localdate().isoformat()
    if tool_name == TOOL_GET_AGENTS_LISTING and "limit" not in tool_args:
        tool_args["limit"] = 50

    return {
        "name": tool_name,
        "call_id": "auto_required_query_tool_call",
        "arguments": tool_args,
    }


def run_chat(
    user,
    text: str,
    conversation_id: int | None,
    origin: str | None = AssistantConversationOrigin.WIDGET,
    history_messages: list[dict] | None = None,
    assistant_context: dict | None = None,
    persist_history: bool = True,
):
    conversation = None
    answer = ASSISTANT_TEMPORARY_FAILURE_RESPONSE
    answer_payload = {}
    final_response_status = AUDIT_STATUS_FAIL_SAFE
    scope_classification = ""
    capability_classification = ""
    capability_id = ""
    block_reason = ""
    fallback_reason = ""
    tools_attempted: list[str] = []
    tools_succeeded: list[str] = []
    current_assistant_context = {}
    semantic_resolution = None
    semantic_audit_payload = {}
    resolved_text = text
    processing_trace = ProcessingStatusTrace()
    pipeline_trace = _build_initial_pipeline_trace(text, {})
    scope_guardrail_enabled = is_scope_guardrail_enabled()
    capability_guardrail_enabled = is_capability_guardrail_enabled()
    output_scope_guardrail_enabled = is_output_scope_guardrail_enabled()
    output_truthfulness_guardrail_enabled = is_output_truthfulness_guardrail_enabled()
    allow_period_context_inheritance = False
    output_validation_summary = _build_output_validation_summary(
        output_scope_guardrail_enabled=output_scope_guardrail_enabled,
        output_truthfulness_guardrail_enabled=output_truthfulness_guardrail_enabled,
    )

    try:
        logger.info(
            "assistant.chat.request user_id=%s origin=%s persist_history=%s conversation_id=%s scope_guardrail_enabled=%s capability_guardrail_enabled=%s output_scope_guardrail_enabled=%s output_truthfulness_guardrail_enabled=%s input_text=%s",
            getattr(user, "id", None),
            origin,
            persist_history,
            conversation_id,
            scope_guardrail_enabled,
            capability_guardrail_enabled,
            output_scope_guardrail_enabled,
            output_truthfulness_guardrail_enabled,
            _truncate_for_log(text),
        )
        processing_trace.emit(PROCESSING_STATUS_UNDERSTANDING_QUERY)
        input_messages = []
        if persist_history:
            conversation = _resolve_conversation(user, conversation_id, origin=origin)
            _save_user_message(conversation, text)
            input_messages = _conversation_messages_for_context(conversation)
            current_assistant_context = (
                conversation.context_json if isinstance(conversation.context_json, dict) else {}
            )
            allow_period_context_inheritance = conversation is not None
        else:
            input_messages = _sanitize_history_messages(history_messages)
            input_messages.append(
                {
                    "role": AssistantMessageRole.USER,
                    "content": text,
                }
            )
            current_assistant_context = assistant_context if isinstance(assistant_context, dict) else {}
            allow_period_context_inheritance = False

        pipeline_trace = _build_initial_pipeline_trace(text, current_assistant_context)

        processing_trace.emit(PROCESSING_STATUS_CHECKING_CONTEXT)
        processing_trace.emit(PROCESSING_STATUS_RESOLVING_INTENT)
        semantic_resolution = resolve_semantic_operational_query(
            text,
            current_assistant_context,
            allow_period_context_inheritance=allow_period_context_inheritance,
        )
        semantic_audit_payload = semantic_resolution.to_audit_dict()
        pipeline_trace["resolved_intent"] = semantic_resolution.intent or ""
        pipeline_trace["resolved_context"]["semantic_resolution"] = semantic_audit_payload
        if semantic_resolution.expanded_text:
            resolved_text = semantic_resolution.expanded_text
        if semantic_resolution.semantic_applied:
            current_assistant_context = merge_semantic_context(
                current_assistant_context,
                semantic_resolution,
            )
        pipeline_trace["resolved_context"]["context_after"] = _build_trace_context_snapshot(
            current_assistant_context
        )
        logger.info(
            "assistant.chat.semantic_resolution semantic_applied=%s intent=%s reason=%s resolved_text=%s",
            semantic_resolution.semantic_applied,
            semantic_resolution.intent or "",
            semantic_resolution.reason or "",
            _truncate_for_log(resolved_text),
        )

        if scope_guardrail_enabled:
            scope_validation = _safe_validate_input(resolved_text)
        else:
            scope_validation = _scope_validation_when_guardrail_disabled()
        scope_classification = scope_validation.classification
        logger.info(
            "assistant.chat.scope_validation enabled=%s classification=%s reason=%s matched_terms=%s",
            scope_guardrail_enabled,
            scope_validation.classification,
            scope_validation.reason,
            ",".join(scope_validation.matched_terms),
        )
        if scope_validation.classification == FORA_DO_ESCOPO:
            logger.info(
                "Mensagem bloqueada pelo guardrail de escopo. reason=%s matched_terms=%s",
                scope_validation.reason,
                ",".join(scope_validation.matched_terms),
            )
            processing_trace.emit_many(
                PROCESSING_STATUS_BUILDING_RESPONSE,
                PROCESSING_STATUS_VALIDATING_RESPONSE,
            )
            answer = scope_validation.response or ASSISTANT_OUT_OF_SCOPE_RESPONSE
            answer_payload = {}
            block_reason = scope_validation.reason
            final_response_status = AUDIT_STATUS_BLOCKED_SCOPE
            pipeline_trace["reason_no_data"] = scope_validation.reason or ""
            pipeline_trace["final_answer_type"] = "blocked_scope"
            processing_trace.finalize_completed()
        else:
            openai_settings = get_openai_settings()
            if not openai_settings["enabled"]:
                processing_trace.emit_many(
                    PROCESSING_STATUS_BUILDING_RESPONSE,
                    PROCESSING_STATUS_VALIDATING_RESPONSE,
                )
                answer = ASSISTANT_DISABLED_RESPONSE
                answer_payload = {}
                final_response_status = AUDIT_STATUS_DISABLED
                pipeline_trace["final_answer_type"] = "assistant_disabled"
                processing_trace.finalize_completed()
            else:
                if capability_guardrail_enabled:
                    capability_assessment = _safe_assess_capability(resolved_text)
                else:
                    capability_assessment = _capability_assessment_when_guardrail_disabled()
                capability_classification = capability_assessment.category
                capability_id = capability_assessment.capability_id
                logger.info(
                    "assistant.chat.capability_assessment enabled=%s category=%s capability_id=%s reason=%s allowed_tools=%s",
                    capability_guardrail_enabled,
                    capability_assessment.category,
                    capability_assessment.capability_id,
                    capability_assessment.reason,
                    ",".join(capability_assessment.allowed_tools),
                )
                if not pipeline_trace["resolved_intent"]:
                    pipeline_trace["resolved_intent"] = capability_id

                if semantic_resolution and semantic_resolution.clarification_response:
                    capability_classification = "CONSULTA_SUPORTADA"
                    capability_id = semantic_resolution.intent or "semantic_clarification"
                    processing_trace.emit_many(
                        PROCESSING_STATUS_BUILDING_RESPONSE,
                        PROCESSING_STATUS_VALIDATING_RESPONSE,
                    )
                    answer = semantic_resolution.clarification_response
                    answer_payload = {}
                    logger.info(
                        "Resolucao semantica respondeu com esclarecimento. intent=%s reason=%s",
                        semantic_resolution.intent,
                        semantic_resolution.reason,
                    )
                    pipeline_trace["final_answer_type"] = "semantic_clarification"
                    final_response_status = AUDIT_STATUS_COMPLETED
                    processing_trace.finalize_completed()
                elif capability_assessment.category == NAO_SUPORTADA:
                    logger.info(
                        "Mensagem recusada por capacidade. capability_id=%s reason=%s origin=%s",
                        capability_assessment.capability_id,
                        capability_assessment.reason,
                        origin,
                    )
                    processing_trace.emit_many(
                        PROCESSING_STATUS_BUILDING_RESPONSE,
                        PROCESSING_STATUS_VALIDATING_RESPONSE,
                    )
                    answer = (
                        capability_assessment.unsupported_response
                        or ASSISTANT_UNVERIFIED_RESPONSE
                    )
                    answer_payload = {}
                    block_reason = capability_assessment.reason
                    final_response_status = AUDIT_STATUS_BLOCKED_CAPABILITY
                    pipeline_trace["reason_no_data"] = capability_assessment.reason or ""
                    pipeline_trace["final_answer_type"] = "blocked_capability"
                    processing_trace.finalize_completed()
                elif capability_assessment.direct_response:
                    processing_trace.emit_many(
                        PROCESSING_STATUS_BUILDING_RESPONSE,
                        PROCESSING_STATUS_VALIDATING_RESPONSE,
                    )
                    answer = capability_assessment.direct_response
                    answer_payload = {}
                    final_response_status = AUDIT_STATUS_COMPLETED
                    pipeline_trace["final_answer_type"] = "direct_response"
                    processing_trace.finalize_completed()
                else:
                    try:
                        client = get_openai_client()
                        tools_schema = _filter_tools_schema(
                            get_tools_schema(),
                            capability_assessment.allowed_tools,
                        )
                        response = _call_model(
                            client=client,
                            settings=openai_settings,
                            input_payload=_build_responses_input_from_messages(
                                input_messages,
                                capability_instruction=build_capability_instruction(
                                    capability_assessment
                                ),
                                context_instruction=format_productivity_context_instruction(
                                    current_assistant_context,
                                    allow_period_inheritance=allow_period_context_inheritance,
                                ),
                                semantic_instruction=format_semantic_resolution_instruction(
                                    semantic_resolution
                                ),
                            ),
                            tools_schema=tools_schema,
                        )

                        executed_calls = 0
                        fail_safe_answer = None
                        tool_records = []
                        stop_after_tool_issue = False
                        while executed_calls < MAX_TOOL_CALLS_PER_REQUEST:
                            tool_calls = _extract_tool_calls(response)
                            if not tool_calls:
                                break

                            tool_outputs = []
                            for call in tool_calls:
                                if executed_calls >= MAX_TOOL_CALLS_PER_REQUEST:
                                    break

                                tools_attempted.append(call["name"])
                                if call["name"] in capability_assessment.query_tools:
                                    processing_trace.emit(PROCESSING_STATUS_QUERYING_DATABASE)
                                processing_trace.emit(PROCESSING_STATUS_RUNNING_TOOL)
                                merged_tool_args, reused_context = _merge_tool_args_with_context(
                                    call,
                                    current_assistant_context,
                                    semantic_resolution,
                                    allow_period_context_inheritance=allow_period_context_inheritance,
                                )
                                call["arguments"] = merged_tool_args
                                if not pipeline_trace["tool_selected"]:
                                    pipeline_trace["tool_selected"] = call["name"]
                                    pipeline_trace["tool_args"] = deepcopy(merged_tool_args)
                                if reused_context:
                                    logger.info(
                                        "Contexto anterior reutilizado para consulta analitica. conversation_id=%s capability_id=%s start_date=%s end_date=%s",
                                        getattr(conversation, "id", None),
                                        capability_assessment.capability_id,
                                        merged_tool_args.get("date_from"),
                                        merged_tool_args.get("date_to"),
                                    )
                                if (
                                    capability_assessment.allowed_tools
                                    and call["name"] not in capability_assessment.allowed_tools
                                ):
                                    logger.warning(
                                        "Modelo tentou usar tool fora da capacidade validada. tool=%s capability=%s",
                                        call["name"],
                                        capability_assessment.capability_id,
                                    )
                                    fail_safe_answer = (
                                        capability_assessment.unverified_response
                                        or ASSISTANT_UNVERIFIED_RESPONSE
                                    )
                                    fallback_reason = FALLBACK_REASON_TOOL_OUTSIDE_VALIDATED_CAPABILITY
                                    break

                                result, status = _execute_tool_with_audit(conversation, user, call)
                                tool_rows = _tool_result_rows(result if isinstance(result, dict) else {})
                                tool_preview = _tool_result_preview(result if isinstance(result, dict) else {})
                                pipeline_trace["tool_trace"].append(
                                    {
                                        "tool_name": call["name"],
                                        "tool_args": deepcopy(merged_tool_args),
                                        "status": status,
                                        "rows": tool_rows,
                                        "reason_no_data": (
                                            result.get("reason_no_data")
                                            if isinstance(result, dict)
                                            else ""
                                        ),
                                        "preview": tool_preview,
                                        "exception": (
                                            result.get("detail")
                                            if isinstance(result, dict)
                                            and status == AssistantActionLogStatus.ERROR
                                            else ""
                                        ),
                                    }
                                )
                                if status == AssistantActionLogStatus.SUCCESS:
                                    pipeline_trace["tool_result_rows"] = tool_rows
                                    pipeline_trace["tool_result_preview"] = tool_preview
                                    pipeline_trace["reason_no_data"] = (
                                        result.get("reason_no_data") or ""
                                        if isinstance(result, dict)
                                        else pipeline_trace["reason_no_data"]
                                    )
                                tool_records.append(
                                    build_tool_execution_record(call["name"], status, result)
                                )
                                if status == AssistantActionLogStatus.SUCCESS:
                                    tools_succeeded.append(call["name"])
                                    if call["name"] in capability_assessment.query_tools:
                                        processing_trace.emit(PROCESSING_STATUS_FILTERING_RESULTS)
                                    if call["name"] == "get_productivity_analytics":
                                        productivity_context = build_productivity_context(
                                            call["arguments"],
                                            result,
                                        )
                                        if productivity_context is not None:
                                            current_assistant_context = merge_productivity_context(
                                                current_assistant_context,
                                                productivity_context,
                                            )
                                            if semantic_resolution is not None:
                                                semantic_resolution = (
                                                    _sync_semantic_resolution_with_productivity_result(
                                                        semantic_resolution,
                                                        productivity_context,
                                                    )
                                                )
                                                current_assistant_context = merge_semantic_context(
                                                    current_assistant_context,
                                                    semantic_resolution,
                                                )
                                if status == AssistantActionLogStatus.ERROR:
                                    stop_after_tool_issue = True
                                    break
                                try:
                                    serialized_tool_output = json.dumps(result, ensure_ascii=False)
                                    logger.info(
                                        "assistant.tool.output.serialized tool=%s bytes=%s conversation_id=%s",
                                        call["name"],
                                        len(serialized_tool_output.encode("utf-8")),
                                        getattr(conversation, "id", None),
                                    )
                                except Exception:
                                    logger.exception(
                                        "assistant.tool.output.serialize_failed tool=%s conversation_id=%s result_type=%s",
                                        call["name"],
                                        getattr(conversation, "id", None),
                                        type(result).__name__,
                                    )
                                    raise
                                tool_outputs.append(
                                    {
                                        "type": "function_call_output",
                                        "call_id": call["call_id"],
                                        "output": serialized_tool_output,
                                    }
                                )
                                executed_calls += 1

                            if fail_safe_answer:
                                answer = fail_safe_answer
                                final_response_status = AUDIT_STATUS_FAIL_SAFE
                                break

                            if stop_after_tool_issue:
                                break

                            if not tool_outputs:
                                break
                            if _should_finalize_after_tool(capability_assessment, tool_records):
                                logger.info(
                                    "assistant.tool.finalized_without_second_model_call capability_id=%s tool_selected=%s tool_rows=%s limit=%s",
                                    capability_assessment.capability_id,
                                    pipeline_trace.get("tool_selected") or "",
                                    pipeline_trace.get("tool_result_rows") or 0,
                                    (pipeline_trace.get("tool_args") or {}).get("limit"),
                                )
                                break

                            response = _call_model(
                                client=client,
                                settings=openai_settings,
                                input_payload=tool_outputs,
                                tools_schema=tools_schema,
                                previous_response_id=getattr(response, "id", None),
                            )

                        if (
                            not fail_safe_answer
                            and capability_assessment.query_tools
                            and not any(
                                record.name in capability_assessment.query_tools
                                for record in tool_records
                            )
                        ):
                            auto_call = _build_required_query_tool_call(
                                capability_assessment,
                                semantic_resolution,
                                allow_period_context_inheritance=allow_period_context_inheritance,
                            )
                            if auto_call is not None:
                                logger.info(
                                    "Executando tool obrigatoria em fallback backend. capability_id=%s tool=%s",
                                    capability_assessment.capability_id,
                                    auto_call["name"],
                                )
                                tools_attempted.append(auto_call["name"])
                                processing_trace.emit(PROCESSING_STATUS_QUERYING_DATABASE)
                                processing_trace.emit(PROCESSING_STATUS_RUNNING_TOOL)
                                merged_tool_args, reused_context = _merge_tool_args_with_context(
                                    auto_call,
                                    current_assistant_context,
                                    semantic_resolution,
                                    allow_period_context_inheritance=allow_period_context_inheritance,
                                )
                                auto_call["arguments"] = merged_tool_args
                                if not pipeline_trace["tool_selected"]:
                                    pipeline_trace["tool_selected"] = auto_call["name"]
                                    pipeline_trace["tool_args"] = deepcopy(merged_tool_args)
                                if reused_context:
                                    logger.info(
                                        "Contexto anterior reutilizado para fallback de tool obrigatoria. conversation_id=%s capability_id=%s",
                                        getattr(conversation, "id", None),
                                        capability_assessment.capability_id,
                                    )

                                result, status = _execute_tool_with_audit(conversation, user, auto_call)
                                tool_rows = _tool_result_rows(result if isinstance(result, dict) else {})
                                tool_preview = _tool_result_preview(result if isinstance(result, dict) else {})
                                pipeline_trace["tool_trace"].append(
                                    {
                                        "tool_name": auto_call["name"],
                                        "tool_args": deepcopy(merged_tool_args),
                                        "status": status,
                                        "rows": tool_rows,
                                        "reason_no_data": (
                                            result.get("reason_no_data")
                                            if isinstance(result, dict)
                                            else ""
                                        ),
                                        "preview": tool_preview,
                                        "exception": (
                                            result.get("detail")
                                            if isinstance(result, dict)
                                            and status == AssistantActionLogStatus.ERROR
                                            else ""
                                        ),
                                    }
                                )
                                if status == AssistantActionLogStatus.SUCCESS:
                                    tools_succeeded.append(auto_call["name"])
                                    pipeline_trace["tool_result_rows"] = tool_rows
                                    pipeline_trace["tool_result_preview"] = tool_preview
                                    pipeline_trace["reason_no_data"] = (
                                        result.get("reason_no_data") or ""
                                        if isinstance(result, dict)
                                        else pipeline_trace["reason_no_data"]
                                    )
                                    processing_trace.emit(PROCESSING_STATUS_FILTERING_RESULTS)
                                    if auto_call["name"] == TOOL_GET_PRODUCTIVITY_ANALYTICS:
                                        productivity_context = build_productivity_context(
                                            auto_call["arguments"],
                                            result,
                                        )
                                        if productivity_context is not None:
                                            current_assistant_context = merge_productivity_context(
                                                current_assistant_context,
                                                productivity_context,
                                            )
                                            if semantic_resolution is not None:
                                                semantic_resolution = (
                                                    _sync_semantic_resolution_with_productivity_result(
                                                        semantic_resolution,
                                                        productivity_context,
                                                    )
                                                )
                                                current_assistant_context = merge_semantic_context(
                                                    current_assistant_context,
                                                    semantic_resolution,
                                                )
                                if status == AssistantActionLogStatus.ERROR:
                                    stop_after_tool_issue = True
                                tool_records.append(
                                    build_tool_execution_record(auto_call["name"], status, result)
                                )
                                executed_calls += 1

                        runtime_validation = _safe_evaluate_capability_runtime(
                            capability_assessment,
                            tool_records,
                        )
                        runtime_diagnostics = _runtime_tool_diagnostics(
                            capability_assessment,
                            tool_records,
                        )
                        if runtime_validation.classification == SUPORTADA_MAS_SEM_DADOS:
                            logger.info(
                                (
                                    "Consulta sem dados suficientes. capability_id=%s origin=%s reason=%s "
                                    "query_attempted=%s query_success=%s query_has_data_flags=%s "
                                    "query_reason_no_data=%s"
                                ),
                                capability_assessment.capability_id,
                                origin,
                                runtime_validation.reason,
                                runtime_diagnostics["query_attempted"],
                                runtime_diagnostics["query_success"],
                                runtime_diagnostics["query_has_data_flags"],
                                runtime_diagnostics["query_reason_no_data"],
                            )
                            processing_trace.emit_many(
                                PROCESSING_STATUS_BUILDING_RESPONSE,
                                PROCESSING_STATUS_VALIDATING_RESPONSE,
                            )
                            analytics_result = _first_successful_tool_result(
                                tool_records,
                                TOOL_GET_PRODUCTIVITY_ANALYTICS,
                            )
                            agents_listing_result = _first_successful_tool_result(
                                tool_records,
                                TOOL_GET_AGENTS_LISTING,
                            )
                            no_data_response = (
                                runtime_validation.response
                                or capability_assessment.no_data_response
                            )
                            if capability_assessment.capability_id == PRODUCTIVITY_ANALYTICS_CAPABILITY_ID:
                                no_data_response = (
                                    _build_productivity_no_data_response(analytics_result or {})
                                    or no_data_response
                                )
                            elif capability_assessment.capability_id == "agent_listing_query":
                                no_data_response = (
                                    _build_agents_listing_no_data_response(agents_listing_result or {})
                                    or no_data_response
                                )
                            answer = (
                                no_data_response
                            )
                            answer_payload = {}
                            fallback_reason = runtime_validation.reason
                            final_response_status = AUDIT_STATUS_NO_DATA
                            pipeline_trace["reason_no_data"] = runtime_validation.reason or ""
                            pipeline_trace["final_answer_type"] = "no_data"
                            processing_trace.finalize_completed()
                        elif runtime_validation.classification == FORA_DO_ESCOPO:
                            logger.info(
                                (
                                    "Validacao de runtime bloqueou resposta. capability_id=%s origin=%s reason=%s "
                                    "query_attempted=%s query_success=%s query_has_data_flags=%s "
                                    "query_reason_no_data=%s"
                                ),
                                capability_assessment.capability_id,
                                origin,
                                runtime_validation.reason,
                                runtime_diagnostics["query_attempted"],
                                runtime_diagnostics["query_success"],
                                runtime_diagnostics["query_has_data_flags"],
                                runtime_diagnostics["query_reason_no_data"],
                            )
                            processing_trace.emit_many(
                                PROCESSING_STATUS_BUILDING_RESPONSE,
                                PROCESSING_STATUS_VALIDATING_RESPONSE,
                            )
                            answer = (
                                runtime_validation.response
                                or capability_assessment.unverified_response
                            )
                            answer_payload = {}
                            fallback_reason = runtime_validation.reason
                            if runtime_validation.reason in TOOL_FAILURE_REASONS:
                                logger.warning(
                                    "Falha de tool registrada na validacao de runtime. capability_id=%s reason=%s",
                                    capability_assessment.capability_id,
                                    runtime_validation.reason,
                                )
                                final_response_status = AUDIT_STATUS_TOOL_FAILURE
                                pipeline_trace["final_answer_type"] = "tool_failure"
                            else:
                                final_response_status = AUDIT_STATUS_FAIL_SAFE
                                pipeline_trace["final_answer_type"] = "runtime_fail_safe"
                            pipeline_trace["reason_no_data"] = runtime_validation.reason or ""
                            processing_trace.finalize_failed()
                        elif fail_safe_answer:
                            processing_trace.emit_many(
                                PROCESSING_STATUS_BUILDING_RESPONSE,
                                PROCESSING_STATUS_VALIDATING_RESPONSE,
                            )
                            answer = fail_safe_answer
                            answer_payload = {}
                            final_response_status = AUDIT_STATUS_FAIL_SAFE
                            pipeline_trace["final_answer_type"] = "fail_safe"
                            processing_trace.finalize_failed()
                        else:
                            deterministic_answer = None
                            deterministic_payload = None
                            if capability_assessment.capability_id == PRODUCTIVITY_ANALYTICS_CAPABILITY_ID:
                                analytics_result = _first_successful_tool_result(
                                    tool_records,
                                    TOOL_GET_PRODUCTIVITY_ANALYTICS,
                                )
                                try:
                                    deterministic_answer = _build_productivity_analytics_response(
                                        analytics_result or {}
                                    )
                                    deterministic_payload = _build_productivity_analytics_payload(
                                        analytics_result or {},
                                        deterministic_answer,
                                    )
                                except Exception:
                                    logger.exception(
                                        "assistant.productivity.deterministic_build_failed conversation_id=%s tool_rows=%s reason_no_data=%s",
                                        getattr(conversation, "id", None),
                                        len((analytics_result or {}).get("ranking") or []),
                                        (analytics_result or {}).get("reason_no_data"),
                                    )
                                    raise
                                if analytics_result:
                                    logger.info(
                                        "Tool analytics retornou ranking_size=%s reason_no_data=%s response_source=%s",
                                        len(analytics_result.get("ranking") or []),
                                        analytics_result.get("reason_no_data"),
                                        "backend_deterministic" if deterministic_answer else "model",
                                    )
                                    pipeline_trace["tool_result_rows"] = len(analytics_result.get("ranking") or [])
                                    pipeline_trace["tool_result_preview"] = _tool_result_preview(analytics_result)
                                    pipeline_trace["reason_no_data"] = analytics_result.get("reason_no_data") or ""
                            elif capability_assessment.capability_id == "agent_listing_query":
                                agents_result = _first_successful_tool_result(
                                    tool_records,
                                    TOOL_GET_AGENTS_LISTING,
                                )
                                deterministic_answer = _build_agents_listing_response(
                                    agents_result or {}
                                )
                                deterministic_payload = _build_agents_listing_payload(
                                    agents_result or {},
                                    deterministic_answer,
                                )
                                if agents_result:
                                    logger.info(
                                        "Tool de listagem de agentes retornou total_found=%s reason_no_data=%s response_source=%s",
                                        agents_result.get("total_found"),
                                        agents_result.get("reason_no_data"),
                                        "backend_deterministic" if deterministic_answer else "model",
                                    )
                                    pipeline_trace["tool_result_rows"] = len(agents_result.get("items") or [])
                                    pipeline_trace["tool_result_preview"] = _tool_result_preview(agents_result)
                                    pipeline_trace["reason_no_data"] = agents_result.get("reason_no_data") or ""
                            if deterministic_answer:
                                logger.info(
                                    "assistant.structured_response.completed capability=%s tool_selected=%s tool_rows=%s limit=%s",
                                    capability_assessment.capability_id,
                                    pipeline_trace.get("tool_selected") or "",
                                    pipeline_trace.get("tool_result_rows") or 0,
                                    (pipeline_trace.get("tool_args") or {}).get("limit"),
                                )

                            processing_trace.emit(PROCESSING_STATUS_BUILDING_RESPONSE)
                            answer = deterministic_answer or _extract_response_text(response)
                            answer_payload = deterministic_payload or {}
                            if not answer:
                                processing_trace.emit(PROCESSING_STATUS_VALIDATING_RESPONSE)
                                answer = (
                                    capability_assessment.unverified_response
                                    or ASSISTANT_UNVERIFIED_RESPONSE
                                )
                                answer_payload = {}
                                fallback_reason = FALLBACK_REASON_EMPTY_MODEL_OUTPUT
                                final_response_status = AUDIT_STATUS_FAIL_SAFE
                                pipeline_trace["reason_no_data"] = FALLBACK_REASON_EMPTY_MODEL_OUTPUT
                                pipeline_trace["final_answer_type"] = "empty_model_output"
                                processing_trace.finalize_failed()
                            else:
                                processing_trace.emit(PROCESSING_STATUS_VALIDATING_RESPONSE)
                                output_validation, output_validation_summary = _safe_validate_output(
                                    user_text=text,
                                    answer=answer,
                                    had_tool_calls=executed_calls > 0,
                                    assessment=capability_assessment,
                                    tool_records=tool_records,
                                    output_scope_guardrail_enabled=output_scope_guardrail_enabled,
                                    output_truthfulness_guardrail_enabled=output_truthfulness_guardrail_enabled,
                                )
                                if output_validation.classification == FORA_DO_ESCOPO:
                                    logger.warning(
                                        "Resposta final bloqueada pela pos-validacao. reason=%s conversation_id=%s",
                                        output_validation.reason,
                                        getattr(conversation, "id", None),
                                    )
                                    answer = (
                                        output_validation.response
                                        or capability_assessment.unverified_response
                                        or ASSISTANT_UNVERIFIED_RESPONSE
                                    )
                                    answer_payload = {}
                                    fallback_reason = output_validation.reason
                                    final_response_status = AUDIT_STATUS_FAIL_SAFE
                                    pipeline_trace["reason_no_data"] = output_validation.reason or ""
                                    pipeline_trace["final_answer_type"] = "output_validation_blocked"
                                    processing_trace.finalize_failed()
                                else:
                                    logger.info(
                                        "Fluxo principal concluido com sucesso. capability_id=%s tools_attempted=%s tools_succeeded=%s origin=%s response_source=%s",
                                        capability_assessment.capability_id,
                                        len(tools_attempted),
                                        len(tools_succeeded),
                                        origin,
                                        "backend_deterministic" if deterministic_answer else "model",
                                    )
                                    final_response_status = AUDIT_STATUS_COMPLETED
                                    pipeline_trace["final_answer_type"] = (
                                        "backend_deterministic"
                                        if deterministic_answer
                                        else "model_response"
                                    )
                                    processing_trace.finalize_completed()
                    except OpenAIConfigError as exc:
                        logger.warning(
                            "Falha de configuracao do assistente: OPENAI_API_KEY ausente."
                        )
                        processing_trace.emit_many(
                            PROCESSING_STATUS_BUILDING_RESPONSE,
                            PROCESSING_STATUS_VALIDATING_RESPONSE,
                        )
                        answer = ASSISTANT_CONFIG_ERROR_RESPONSE
                        answer_payload = {}
                        fallback_reason = FALLBACK_REASON_OPENAI_CONFIG_ERROR
                        final_response_status = AUDIT_STATUS_CONFIG_ERROR
                        pipeline_trace["reason_no_data"] = FALLBACK_REASON_OPENAI_CONFIG_ERROR
                        pipeline_trace["final_answer_type"] = "openai_config_error"
                        pipeline_trace["exception"] = str(exc)
                        processing_trace.finalize_failed()
                    except Exception as exc:
                        logger.exception(
                            "Falha ao chamar OpenAI Responses API. capability_id=%s tool_selected=%s tool_attempted=%s tool_executed=%s tool_args=%s reason_no_data=%s",
                            getattr(capability_assessment, "capability_id", ""),
                            pipeline_trace.get("tool_selected"),
                            bool(tools_attempted),
                            bool(tools_succeeded),
                            pipeline_trace.get("tool_args"),
                            pipeline_trace.get("reason_no_data"),
                        )
                        processing_trace.emit_many(
                            PROCESSING_STATUS_BUILDING_RESPONSE,
                            PROCESSING_STATUS_VALIDATING_RESPONSE,
                        )
                        answer = ASSISTANT_TEMPORARY_FAILURE_RESPONSE
                        answer_payload = {}
                        fallback_reason = FALLBACK_REASON_OPENAI_RUNTIME_ERROR
                        final_response_status = AUDIT_STATUS_TEMPORARY_FAILURE
                        pipeline_trace["reason_no_data"] = FALLBACK_REASON_OPENAI_RUNTIME_ERROR
                        pipeline_trace["final_answer_type"] = "openai_runtime_error"
                        pipeline_trace["exception"] = str(exc)
                        processing_trace.finalize_failed()

        if persist_history and conversation is not None:
            if conversation.context_json != current_assistant_context:
                conversation.context_json = current_assistant_context
                conversation.save(update_fields=["context_json", "updated_at"])
            _save_assistant_message(conversation, answer, payload=answer_payload)
        pipeline_trace["resolved_context"]["context_after"] = _build_trace_context_snapshot(
            current_assistant_context
        )
        logger.info(
            "assistant.chat.response status=%s final_answer_type=%s block_reason=%s fallback_reason=%s scope_classification=%s capability_classification=%s capability_id=%s conversation_id=%s answer_preview=%s",
            final_response_status,
            pipeline_trace.get("final_answer_type") or "",
            block_reason,
            fallback_reason,
            scope_classification,
            capability_classification,
            capability_id,
            getattr(conversation, "id", None),
            _truncate_for_log(answer),
        )
        pipeline_trace["output_validation"] = deepcopy(output_validation_summary)
        _log_pipeline_trace(pipeline_trace)
        response_payload = {
            "conversation_id": conversation.id if conversation is not None else None,
            "answer": answer,
            "answer_payload": answer_payload,
            "assistant_context": current_assistant_context,
            "processing_statuses": processing_trace.serialize(),
            "processing_status": (
                processing_trace.items[-1] if processing_trace.items else PROCESSING_STATUS_COMPLETED
            ),
            "debug_trace": deepcopy(pipeline_trace) if getattr(settings, "ASSISTANT_DEBUG", False) else {},
        }
        response_payload.update(
            _build_response_diagnostics(
                user=user,
                final_response_status=final_response_status,
                fallback_reason=fallback_reason,
                output_validation=output_validation_summary,
                capability_id=capability_id,
                pipeline_trace=pipeline_trace,
                tools_attempted=tools_attempted,
                tools_succeeded=tools_succeeded,
            )
        )
        return response_payload
    except AssistantConversationLimitError as exc:
        logger.info("Limite de conversas persistidas atingido para user_id=%s", user.id)
        answer = build_conversation_limit_response(exc.limit)
        answer_payload = {}
        block_reason = BLOCK_REASON_CONVERSATION_LIMIT_REACHED
        final_response_status = AUDIT_STATUS_BLOCKED_LIMIT
        pipeline_trace["reason_no_data"] = BLOCK_REASON_CONVERSATION_LIMIT_REACHED
        pipeline_trace["final_answer_type"] = "blocked_limit"
        pipeline_trace["exception"] = str(exc)
        processing_trace.emit_many(
            PROCESSING_STATUS_BUILDING_RESPONSE,
            PROCESSING_STATUS_VALIDATING_RESPONSE,
        )
        processing_trace.finalize_completed()
        logger.info(
            "assistant.chat.response status=%s final_answer_type=%s block_reason=%s fallback_reason=%s scope_classification=%s capability_classification=%s capability_id=%s conversation_id=%s answer_preview=%s",
            final_response_status,
            pipeline_trace.get("final_answer_type") or "",
            block_reason,
            fallback_reason,
            scope_classification,
            capability_classification,
            capability_id,
            getattr(conversation, "id", None),
            _truncate_for_log(answer),
        )
        pipeline_trace["output_validation"] = deepcopy(output_validation_summary)
        _log_pipeline_trace(pipeline_trace)
        response_payload = {
            "conversation_id": None,
            "answer": answer,
            "answer_payload": {},
            "processing_statuses": processing_trace.serialize(),
            "processing_status": processing_trace.items[-1],
            "debug_trace": deepcopy(pipeline_trace) if getattr(settings, "ASSISTANT_DEBUG", False) else {},
        }
        response_payload.update(
            _build_response_diagnostics(
                user=user,
                final_response_status=final_response_status,
                fallback_reason=fallback_reason,
                output_validation=output_validation_summary,
                capability_id=capability_id,
                pipeline_trace=pipeline_trace,
                tools_attempted=tools_attempted,
                tools_succeeded=tools_succeeded,
            )
        )
        return response_payload
    except Exception as exc:
        logger.exception("Falha inesperada no fluxo principal do assistente.")
        answer = ASSISTANT_TEMPORARY_FAILURE_RESPONSE
        answer_payload = {}
        fallback_reason = FALLBACK_REASON_ASSISTANT_RUNTIME_ERROR
        final_response_status = AUDIT_STATUS_TEMPORARY_FAILURE
        pipeline_trace["reason_no_data"] = FALLBACK_REASON_ASSISTANT_RUNTIME_ERROR
        pipeline_trace["final_answer_type"] = "assistant_runtime_error"
        pipeline_trace["exception"] = str(exc)
        processing_trace.emit_many(
            PROCESSING_STATUS_BUILDING_RESPONSE,
            PROCESSING_STATUS_VALIDATING_RESPONSE,
        )
        processing_trace.finalize_failed()
        logger.info(
            "assistant.chat.response status=%s final_answer_type=%s block_reason=%s fallback_reason=%s scope_classification=%s capability_classification=%s capability_id=%s conversation_id=%s answer_preview=%s",
            final_response_status,
            pipeline_trace.get("final_answer_type") or "",
            block_reason,
            fallback_reason,
            scope_classification,
            capability_classification,
            capability_id,
            getattr(conversation, "id", None),
            _truncate_for_log(answer),
        )
        pipeline_trace["output_validation"] = deepcopy(output_validation_summary)
        _log_pipeline_trace(pipeline_trace)
        response_payload = {
            "conversation_id": conversation.id if conversation is not None else None,
            "answer": answer,
            "answer_payload": {},
            "assistant_context": current_assistant_context,
            "processing_statuses": processing_trace.serialize(),
            "processing_status": processing_trace.items[-1],
            "debug_trace": deepcopy(pipeline_trace) if getattr(settings, "ASSISTANT_DEBUG", False) else {},
        }
        response_payload.update(
            _build_response_diagnostics(
                user=user,
                final_response_status=final_response_status,
                fallback_reason=fallback_reason,
                output_validation=output_validation_summary,
                capability_id=capability_id,
                pipeline_trace=pipeline_trace,
                tools_attempted=tools_attempted,
                tools_succeeded=tools_succeeded,
            )
        )
        return response_payload
    finally:
        try:
            record_assistant_audit(
                user=user,
                input_text=text,
                origin=origin,
                event_type=AUDIT_EVENT_CHAT_MESSAGE,
                conversation=conversation,
                scope_classification=scope_classification,
                capability_classification=capability_classification,
                capability_id=capability_id,
                tools_attempted=tools_attempted,
                tools_succeeded=tools_succeeded,
                block_reason=block_reason,
                fallback_reason=fallback_reason,
                final_response_status=final_response_status,
                response_text=answer,
                semantic_resolution=semantic_audit_payload,
                pipeline_trace=pipeline_trace,
            )
        except Exception:
            logger.exception("Falha ao registrar auditoria do assistente.")
