import re

from apps.assistant.models import (
    AssistantConversation,
    AssistantConversationOrigin,
    AssistantConversationStatus,
    AssistantMessageRole,
)
from apps.assistant.services.conversation_store import (
    add_message_to_conversation,
    create_persistent_conversation,
)


ASSISTANT_WIDGET_SESSION_KEY = "assistant_widget_session"
ASSISTANT_WIDGET_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,80}$")


class AssistantWidgetSessionError(Exception):
    pass


class AssistantWidgetEmptySessionError(AssistantWidgetSessionError):
    pass


def validate_widget_session_id(raw_session_id) -> str:
    session_id = str(raw_session_id or "").strip()
    if not ASSISTANT_WIDGET_SESSION_ID_PATTERN.fullmatch(session_id):
        raise AssistantWidgetSessionError("invalid_widget_session_id")
    return session_id


def _new_widget_session_state(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "messages": [],
        "saved_conversation_id": None,
        "assistant_context": {},
    }


def _sanitize_widget_messages(messages) -> list[dict]:
    sanitized = []
    allowed_roles = {
        AssistantMessageRole.USER,
        AssistantMessageRole.ASSISTANT,
        AssistantMessageRole.SYSTEM,
    }
    if not isinstance(messages, list):
        return sanitized

    for item in messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in allowed_roles or not content:
            continue
        payload = item.get("payload")
        sanitized_item = {"role": role, "content": content}
        if isinstance(payload, dict) and payload:
            sanitized_item["payload"] = payload
        sanitized.append(sanitized_item)
    return sanitized


def get_widget_session_state(request, raw_session_id) -> dict:
    session_id = validate_widget_session_id(raw_session_id)
    state = request.session.get(ASSISTANT_WIDGET_SESSION_KEY)

    if not isinstance(state, dict) or state.get("session_id") != session_id:
        state = _new_widget_session_state(session_id)
        request.session[ASSISTANT_WIDGET_SESSION_KEY] = state
        request.session.modified = True
        return state

    state["messages"] = _sanitize_widget_messages(state.get("messages"))
    saved_conversation_id = state.get("saved_conversation_id")
    state["saved_conversation_id"] = saved_conversation_id if isinstance(saved_conversation_id, int) else None
    if not isinstance(state.get("assistant_context"), dict):
        state["assistant_context"] = {}
    request.session[ASSISTANT_WIDGET_SESSION_KEY] = state
    request.session.modified = True
    return state


def get_widget_history_messages(request, raw_session_id) -> list[dict]:
    state = get_widget_session_state(request, raw_session_id)
    return list(state["messages"])


def append_widget_session_messages(request, raw_session_id, messages: list[dict]) -> dict:
    state = get_widget_session_state(request, raw_session_id)
    sanitized_messages = _sanitize_widget_messages(messages)
    if sanitized_messages:
        state["messages"].extend(sanitized_messages)
        request.session[ASSISTANT_WIDGET_SESSION_KEY] = state
        request.session.modified = True
    return state


def get_widget_session_context(request, raw_session_id) -> dict:
    state = get_widget_session_state(request, raw_session_id)
    context = state.get("assistant_context")
    return context if isinstance(context, dict) else {}


def update_widget_session_context(request, raw_session_id, assistant_context: dict | None) -> dict:
    state = get_widget_session_state(request, raw_session_id)
    state["assistant_context"] = assistant_context if isinstance(assistant_context, dict) else {}
    request.session[ASSISTANT_WIDGET_SESSION_KEY] = state
    request.session.modified = True
    return state


def end_widget_session(request, raw_session_id=None) -> bool:
    state = request.session.get(ASSISTANT_WIDGET_SESSION_KEY)
    if not isinstance(state, dict):
        return False

    if raw_session_id is not None:
        try:
            session_id = validate_widget_session_id(raw_session_id)
        except AssistantWidgetSessionError:
            return False
        if state.get("session_id") != session_id:
            return False

    request.session.pop(ASSISTANT_WIDGET_SESSION_KEY, None)
    request.session.modified = True
    return True


def save_widget_session_as_conversation(request, user, raw_session_id):
    state = get_widget_session_state(request, raw_session_id)
    saved_conversation_id = state.get("saved_conversation_id")
    if isinstance(saved_conversation_id, int):
        conversation = AssistantConversation.objects.exclude(
            status=AssistantConversationStatus.DELETED,
        ).filter(
            pk=saved_conversation_id,
            created_by=user,
        ).first()
        if conversation is not None:
            return conversation, True
        state["saved_conversation_id"] = None

    messages = _sanitize_widget_messages(state.get("messages"))
    if not messages:
        raise AssistantWidgetEmptySessionError("empty_widget_session")

    conversation = create_persistent_conversation(
        user,
        origin=AssistantConversationOrigin.WIDGET,
        is_persistent=True,
    )
    for item in messages:
        add_message_to_conversation(
            conversation,
            role=item["role"],
            content=item["content"],
            payload=item.get("payload"),
        )
    if isinstance(state.get("assistant_context"), dict):
        conversation.context_json = state["assistant_context"]
        conversation.save(update_fields=["context_json", "updated_at"])

    state["saved_conversation_id"] = conversation.id
    request.session[ASSISTANT_WIDGET_SESSION_KEY] = state
    request.session.modified = True
    return conversation, False
