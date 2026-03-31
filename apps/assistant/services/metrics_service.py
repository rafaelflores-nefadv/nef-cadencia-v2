from django.db.models import Count, Q

from apps.assistant.models import (
    AssistantActionLog,
    AssistantConversation,
    AssistantConversationStatus,
    AssistantMessage,
    AssistantAuditLog,
)
from apps.assistant.observability import (
    AUDIT_EVENT_CHAT_MESSAGE,
    AUDIT_STATUS_BLOCKED_CAPABILITY,
    AUDIT_STATUS_BLOCKED_SCOPE,
    AUDIT_STATUS_COMPLETED,
    FALLBACK_FINAL_STATUSES,
    INTERACTION_ORIGIN_PAGE,
    INTERACTION_ORIGIN_WIDGET,
    TOOL_EXECUTION_RESULT_ERROR,
)


def _count_by_field(queryset, field_name: str) -> dict[str, int]:
    rows = queryset.values(field_name).annotate(total=Count("id"))
    return {row[field_name]: row["total"] for row in rows if row[field_name]}


def get_assistant_metrics(*, user=None) -> dict:
    conversations = AssistantConversation.objects.exclude(
        status=AssistantConversationStatus.DELETED,
    ).filter(is_persistent=True)
    messages = AssistantMessage.objects.all()
    audits = AssistantAuditLog.objects.all()
    action_logs = AssistantActionLog.objects.all()

    if user is not None:
        conversations = conversations.filter(created_by=user)
        messages = messages.filter(conversation__created_by=user)
        audits = audits.filter(user=user)
        action_logs = action_logs.filter(requested_by=user)

    chat_audits = audits.filter(event_type=AUDIT_EVENT_CHAT_MESSAGE)
    interactions_by_origin = _count_by_field(audits, "origin")
    for origin in (INTERACTION_ORIGIN_WIDGET, INTERACTION_ORIGIN_PAGE):
        interactions_by_origin.setdefault(origin, 0)

    metrics = {
        "scope": "user" if user is not None else "global",
        "user_id": getattr(user, "id", None),
        "messages_total": messages.count(),
        "saved_conversations_total": conversations.count(),
        "interactions_by_origin": interactions_by_origin,
        "events_by_type": _count_by_field(audits, "event_type"),
        "blocked_scope_total": chat_audits.filter(
            final_response_status=AUDIT_STATUS_BLOCKED_SCOPE
        ).count(),
        "blocked_capability_total": chat_audits.filter(
            final_response_status=AUDIT_STATUS_BLOCKED_CAPABILITY
        ).count(),
        "tool_failures_total": action_logs.filter(
            status=TOOL_EXECUTION_RESULT_ERROR
        ).count(),
        "fallbacks_total": chat_audits.filter(
            Q(final_response_status__in=tuple(FALLBACK_FINAL_STATUSES))
            | ~Q(fallback_reason="")
        ).count(),
        "successful_responses_total": chat_audits.filter(
            final_response_status=AUDIT_STATUS_COMPLETED
        ).count(),
    }
    return metrics
