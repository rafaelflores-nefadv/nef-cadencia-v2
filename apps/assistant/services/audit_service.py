from apps.assistant.models import (
    AssistantAuditLog,
)
from apps.assistant.observability import (
    AUDIT_EVENT_CHAT_MESSAGE,
    normalize_audit_event_type,
    normalize_audit_status,
    normalize_block_reason,
    normalize_fallback_reason,
    normalize_interaction_origin,
)
from apps.assistant.services.assistant_config import ASSISTANT_AUDIT_RESPONSE_TEXT_LIMIT


def record_assistant_audit(
    *,
    user,
    input_text: str,
    origin: str | None = None,
    event_type: str | None = AUDIT_EVENT_CHAT_MESSAGE,
    conversation=None,
    scope_classification: str = "",
    capability_classification: str = "",
    capability_id: str = "",
    tools_attempted: list[str] | None = None,
    tools_succeeded: list[str] | None = None,
    block_reason: str = "",
    fallback_reason: str = "",
    final_response_status: str | None = None,
    response_text: str = "",
    semantic_resolution: dict | None = None,
    pipeline_trace: dict | None = None,
):
    return AssistantAuditLog.objects.create(
        conversation=conversation,
        user=user,
        origin=normalize_interaction_origin(origin),
        event_type=normalize_audit_event_type(event_type),
        input_text=input_text,
        scope_classification=scope_classification,
        capability_classification=capability_classification,
        capability_id=capability_id,
        tools_attempted_json=tools_attempted or [],
        tools_succeeded_json=tools_succeeded or [],
        block_reason=normalize_block_reason(block_reason),
        fallback_reason=normalize_fallback_reason(fallback_reason),
        final_response_status=normalize_audit_status(final_response_status),
        response_text=(response_text or "")[:ASSISTANT_AUDIT_RESPONSE_TEXT_LIMIT],
        semantic_resolution_json=semantic_resolution or {},
        pipeline_trace_json=pipeline_trace or {},
    )
