import re

from django.db import transaction
from django.utils import timezone

from apps.assistant.models import (
    AssistantConversation,
    AssistantConversationOrigin,
    AssistantConversationStatus,
    AssistantMessage,
    AssistantMessageRole,
    AssistantUserPreference,
)
from apps.assistant.services.assistant_config import (
    ASSISTANT_CONVERSATION_GENERIC_TITLE_TERMS,
    ASSISTANT_CONVERSATION_TITLE_MAX_LENGTH,
    ASSISTANT_DEFAULT_CONVERSATION_LIMIT,
    ASSISTANT_DEFAULT_CONVERSATION_TITLE,
)
from apps.assistant.services.guardrails import normalize_user_text


class AssistantConversationLimitError(Exception):
    def __init__(self, limit: int):
        super().__init__("conversation_limit_reached")
        self.limit = limit


def get_or_create_user_preference(user):
    if user is None:
        return None
    preference, _ = AssistantUserPreference.objects.get_or_create(
        user=user,
        defaults={"max_saved_conversations": ASSISTANT_DEFAULT_CONVERSATION_LIMIT},
    )
    return preference


def get_user_conversation_limit(user) -> int:
    preference = get_or_create_user_preference(user)
    if preference is None:
        return ASSISTANT_DEFAULT_CONVERSATION_LIMIT
    return preference.max_saved_conversations or ASSISTANT_DEFAULT_CONVERSATION_LIMIT


def validate_user_conversation_limit(user):
    if user is None:
        return
    limit = get_user_conversation_limit(user)
    current_total = AssistantConversation.objects.filter(
        created_by=user,
        is_persistent=True,
    ).exclude(status=AssistantConversationStatus.DELETED).count()
    if current_total >= limit:
        raise AssistantConversationLimitError(limit)


def _normalize_origin(origin: str | None) -> str:
    if origin == AssistantConversationOrigin.PAGE:
        return AssistantConversationOrigin.PAGE
    return AssistantConversationOrigin.WIDGET


def _clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def generate_conversation_title(user_text: str) -> str:
    clean_text = _clean_title(user_text)
    normalized_text = normalize_user_text(clean_text)
    if not clean_text or normalized_text in ASSISTANT_CONVERSATION_GENERIC_TITLE_TERMS:
        return ASSISTANT_DEFAULT_CONVERSATION_TITLE

    if len(clean_text) <= ASSISTANT_CONVERSATION_TITLE_MAX_LENGTH:
        return clean_text

    return (
        clean_text[: ASSISTANT_CONVERSATION_TITLE_MAX_LENGTH - 3].rstrip() + "..."
    )


def build_conversation_title_from_history(conversation: AssistantConversation) -> str:
    user_messages = conversation.messages.filter(
        role=AssistantMessageRole.USER,
    ).order_by("created_at", "id")
    for message in user_messages:
        title = generate_conversation_title(message.content)
        if title != ASSISTANT_DEFAULT_CONVERSATION_TITLE:
            return title
    return ASSISTANT_DEFAULT_CONVERSATION_TITLE


@transaction.atomic
def create_persistent_conversation(
    user,
    *,
    origin: str | None = None,
    is_persistent: bool = True,
):
    if is_persistent:
        validate_user_conversation_limit(user)
    return AssistantConversation.objects.create(
        created_by=user,
        origin=_normalize_origin(origin),
        status=AssistantConversationStatus.ACTIVE,
        is_persistent=is_persistent,
        title=ASSISTANT_DEFAULT_CONVERSATION_TITLE,
    )


def resolve_user_conversation(user, raw_conversation_id, *, origin: str | None = None):
    try:
        conversation_id = int(raw_conversation_id)
    except (TypeError, ValueError):
        conversation_id = None

    if conversation_id is not None:
        conversation = AssistantConversation.objects.exclude(
            status=AssistantConversationStatus.DELETED,
        ).filter(pk=conversation_id).first()
        if conversation is not None and (user.is_staff or conversation.created_by_id == user.id):
            return conversation

    return create_persistent_conversation(user, origin=origin)


def add_message_to_conversation(
    conversation: AssistantConversation,
    *,
    role: str,
    content: str,
    payload: dict | None = None,
):
    message = AssistantMessage.objects.create(
        conversation=conversation,
        role=role,
        content=content,
        payload_json=payload if isinstance(payload, dict) else {},
    )

    conversation.updated_at = timezone.now()
    update_fields = ["updated_at"]
    if role == AssistantMessageRole.USER:
        refreshed_title = build_conversation_title_from_history(conversation)
        if refreshed_title != conversation.title:
            conversation.title = refreshed_title
            update_fields.append("title")
    conversation.save(update_fields=update_fields)
    return message


def list_user_conversations(user):
    return AssistantConversation.objects.filter(
        created_by=user,
    ).exclude(status=AssistantConversationStatus.DELETED)


def delete_conversation(conversation: AssistantConversation, user):
    if not user.is_staff and conversation.created_by_id != user.id:
        raise PermissionError("conversation_access_denied")
    conversation.status = AssistantConversationStatus.DELETED
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["status", "updated_at"])
    return conversation
