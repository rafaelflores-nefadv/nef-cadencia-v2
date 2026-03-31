import json
import logging

from django.conf import settings
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import AssistantConversation, AssistantConversationOrigin, AssistantConversationStatus
from .observability import (
    AUDIT_EVENT_CONVERSATION_DELETED,
    AUDIT_EVENT_PAGE_CONVERSATION_CREATED,
    AUDIT_EVENT_WIDGET_SESSION_ENDED,
    AUDIT_EVENT_WIDGET_SESSION_SAVED,
    AUDIT_STATUS_BLOCKED_LIMIT,
    AUDIT_STATUS_COMPLETED,
    AUDIT_STATUS_FAIL_SAFE,
    BLOCK_REASON_CONVERSATION_LIMIT_REACHED,
    BLOCK_REASON_EMPTY_WIDGET_SESSION,
    BLOCK_REASON_INVALID_WIDGET_SESSION,
)
from .services.assistant_config import ASSISTANT_NAME, build_conversation_limit_response
from .services.audit_service import record_assistant_audit
from .services.assistant_service import run_chat
from .services.processing_status import build_processing_ui_config
from .services.conversation_store import (
    AssistantConversationLimitError,
    create_persistent_conversation,
    delete_conversation,
    get_user_conversation_limit,
    list_user_conversations,
)
from .services.widget_session_service import (
    AssistantWidgetEmptySessionError,
    AssistantWidgetSessionError,
    append_widget_session_messages,
    end_widget_session,
    get_widget_history_messages,
    get_widget_session_context,
    save_widget_session_as_conversation,
    update_widget_session_context,
)


logger = logging.getLogger("assistant")


def _parse_json_body(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _safe_record_assistant_audit(**kwargs):
    try:
        record_assistant_audit(**kwargs)
    except Exception:
        logger.exception("Falha ao registrar auditoria do endpoint do assistente.")


def _serialize_message(message):
    return {
        "role": message.role,
        "content": message.content,
        "payload": message.payload_json if isinstance(message.payload_json, dict) else {},
        "created_at": message.created_at.isoformat(),
    }


def _serialize_conversation_summary(conversation):
    message_count = getattr(conversation, "message_count", None)
    if message_count is None:
        message_count = conversation.messages.count()
    return {
        "id": conversation.id,
        "title": conversation.title,
        "origin": conversation.origin,
        "status": conversation.status,
        "is_persistent": conversation.is_persistent,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "message_count": int(message_count),
    }


def _serialize_conversation_detail(conversation):
    return {
        **_serialize_conversation_summary(conversation),
        "messages": [_serialize_message(message) for message in conversation.messages.all()],
    }


def _page_conversations_queryset(user):
    return (
        list_user_conversations(user)
        .annotate(message_count=Count("messages"))
        .order_by("-updated_at", "-id")
    )


def _get_page_conversation_or_404(user, raw_conversation_id):
    try:
        conversation_id = int(raw_conversation_id)
    except (TypeError, ValueError):
        raise Http404

    conversation = (
        list_user_conversations(user)
        .annotate(message_count=Count("messages"))
        .filter(pk=conversation_id)
        .first()
    )
    if conversation is None:
        raise Http404
    return conversation


@login_required
@require_GET
def assistant_page_view(request):
    conversations = list(_page_conversations_queryset(request.user))
    selected_conversation = None
    selected_raw_id = request.GET.get("conversation_id")
    if selected_raw_id:
        selected_conversation = _get_page_conversation_or_404(request.user, selected_raw_id)
    elif conversations:
        selected_conversation = conversations[0]

    conversation_limit = get_user_conversation_limit(request.user)
    conversation_count = len(conversations)
    conversations_data = [_serialize_conversation_summary(conversation) for conversation in conversations]
    selected_conversation_data = (
        _serialize_conversation_detail(selected_conversation)
        if selected_conversation is not None
        else None
    )

    return render(
        request,
        "assistant/page.html",
        {
            "assistant_name": ASSISTANT_NAME,
            "conversation_limit": conversation_limit,
            "conversation_count": conversation_count,
            "conversation_limit_reached": conversation_count >= conversation_limit,
            "conversations": conversations_data,
            "selected_conversation": selected_conversation_data,
            "assistant_page_initial_data": {
                "assistantName": ASSISTANT_NAME,
                "conversationLimit": conversation_limit,
                "conversationCount": conversation_count,
                "processingUi": build_processing_ui_config(),
                "conversations": conversations_data,
                "selectedConversation": selected_conversation_data,
            },
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def assistant_page_conversations_view(request):
    if request.method == "GET":
        conversations = list(_page_conversations_queryset(request.user))
        conversation_limit = get_user_conversation_limit(request.user)
        return JsonResponse(
            {
                "conversations": [
                    _serialize_conversation_summary(conversation)
                    for conversation in conversations
                ],
                "conversation_count": len(conversations),
                "conversation_limit": conversation_limit,
            }
        )

    try:
        conversation = create_persistent_conversation(
            request.user,
            origin=AssistantConversationOrigin.PAGE,
            is_persistent=True,
        )
    except AssistantConversationLimitError as exc:
        _safe_record_assistant_audit(
            user=request.user,
            origin=AssistantConversationOrigin.PAGE,
            event_type=AUDIT_EVENT_PAGE_CONVERSATION_CREATED,
            input_text="Nova conversa",
            block_reason=BLOCK_REASON_CONVERSATION_LIMIT_REACHED,
            final_response_status=AUDIT_STATUS_BLOCKED_LIMIT,
            response_text=build_conversation_limit_response(exc.limit),
        )
        return JsonResponse(
            {"detail": build_conversation_limit_response(exc.limit)},
            status=409,
        )

    logger.info(
        "Nova conversa persistida criada na pagina. conversation_id=%s user_id=%s",
        conversation.id,
        request.user.id,
    )
    _safe_record_assistant_audit(
        user=request.user,
        conversation=conversation,
        origin=AssistantConversationOrigin.PAGE,
        event_type=AUDIT_EVENT_PAGE_CONVERSATION_CREATED,
        input_text="Nova conversa",
        final_response_status=AUDIT_STATUS_COMPLETED,
        response_text="Conversa persistida criada com sucesso.",
    )
    conversation_count = list_user_conversations(request.user).count()
    return JsonResponse(
        {
            "conversation": _serialize_conversation_summary(conversation),
            "conversation_count": conversation_count,
            "conversation_limit": get_user_conversation_limit(request.user),
        },
        status=201,
    )


@login_required
@require_GET
def assistant_page_conversation_detail_view(request, conversation_id):
    conversation = _get_page_conversation_or_404(request.user, conversation_id)
    return JsonResponse({"conversation": _serialize_conversation_detail(conversation)})


@login_required
@require_POST
def assistant_page_delete_conversation_view(request, conversation_id):
    conversation = _get_page_conversation_or_404(request.user, conversation_id)
    delete_conversation(conversation, request.user)
    logger.info(
        "Conversa persistida excluida. conversation_id=%s user_id=%s",
        conversation.id,
        request.user.id,
    )
    _safe_record_assistant_audit(
        user=request.user,
        conversation=conversation,
        origin=AssistantConversationOrigin.PAGE,
        event_type=AUDIT_EVENT_CONVERSATION_DELETED,
        input_text="Excluir conversa",
        final_response_status=AUDIT_STATUS_COMPLETED,
        response_text="Conversa persistida excluida com sucesso.",
    )
    return JsonResponse(
        {
            "deleted": True,
            "conversation_id": conversation.id,
            "conversation_count": list_user_conversations(request.user).count(),
            "conversation_limit": get_user_conversation_limit(request.user),
        }
    )


@login_required
@require_POST
def assistant_chat_view(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"detail": "Field 'text' is required."}, status=400)

    logger.info(
        "assistant.endpoint.chat.request user_id=%s conversation_id=%s origin=%s text=%s",
        request.user.id,
        payload.get("conversation_id"),
        payload.get("origin"),
        text[:180],
    )

    result = run_chat(
        user=request.user,
        text=text,
        conversation_id=payload.get("conversation_id"),
        origin=payload.get("origin"),
    )
    if result.get("conversation_id"):
        conversation = AssistantConversation.objects.exclude(
            status=AssistantConversationStatus.DELETED,
        ).filter(pk=result["conversation_id"]).first()
        if conversation is not None and (
            request.user.is_staff or conversation.created_by_id == request.user.id
        ):
            result["conversation"] = _serialize_conversation_detail(conversation)
    logger.info(
        "assistant.endpoint.chat.response user_id=%s conversation_id=%s processing_status=%s answer=%s",
        request.user.id,
        result.get("conversation_id"),
        result.get("processing_status"),
        str(result.get("answer") or "")[:180],
    )
    return JsonResponse(result)


@login_required
@require_POST
def assistant_widget_chat_view(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"detail": "Field 'text' is required."}, status=400)

    logger.info(
        "assistant.endpoint.widget_chat.request user_id=%s widget_session_id=%s text=%s",
        request.user.id,
        payload.get("widget_session_id"),
        text[:180],
    )

    widget_session_id = payload.get("widget_session_id")
    try:
        history_messages = get_widget_history_messages(request, widget_session_id)
        assistant_context = get_widget_session_context(request, widget_session_id)
    except AssistantWidgetSessionError:
        return JsonResponse({"detail": "Invalid widget session."}, status=400)

    result = run_chat(
        user=request.user,
        text=text,
        conversation_id=None,
        origin=AssistantConversationOrigin.WIDGET,
        history_messages=history_messages,
        assistant_context=assistant_context,
        persist_history=False,
    )

    session_state = append_widget_session_messages(
        request,
        widget_session_id,
        [
            {"role": "user", "content": text},
            {
                "role": "assistant",
                "content": result["answer"],
                "payload": result.get("answer_payload") if isinstance(result.get("answer_payload"), dict) else {},
            },
        ],
    )
    update_widget_session_context(
        request,
        widget_session_id,
        result.get("assistant_context"),
    )
    logger.info(
        "assistant.endpoint.widget_chat.response user_id=%s widget_session_id=%s processing_status=%s answer=%s saved_conversation_id=%s",
        request.user.id,
        session_state.get("session_id"),
        result.get("processing_status"),
        str(result.get("answer") or "")[:180],
        session_state.get("saved_conversation_id"),
    )
    response_payload = {
        "answer": result["answer"],
        "conversation_id": None,
        "widget_session_id": session_state.get("session_id"),
        "messages": list(session_state.get("messages") or []),
        "assistant_context": result.get("assistant_context") or {},
        "answer_payload": result.get("answer_payload") if isinstance(result.get("answer_payload"), dict) else {},
        "saved_conversation_id": session_state.get("saved_conversation_id"),
        "already_saved": bool(session_state.get("saved_conversation_id")),
    }
    if request.user.is_staff or getattr(settings, "ASSISTANT_DEBUG", False):
        response_payload["final_response_status"] = result.get("final_response_status", "")
        response_payload["fallback_reason"] = result.get("fallback_reason", "")
        response_payload["capability_id"] = result.get("capability_id", "")
        response_payload["tool_selected"] = result.get("tool_selected", "")
        response_payload["tool_attempted"] = bool(result.get("tool_attempted"))
        response_payload["tool_executed"] = bool(result.get("tool_executed"))
        response_payload["reason_no_data"] = result.get("reason_no_data", "")
        response_payload["output_validation"] = (
            result.get("output_validation")
            if isinstance(result.get("output_validation"), dict)
            else {}
        )
    return JsonResponse(response_payload)


@login_required
@require_POST
def assistant_widget_end_session_view(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    ended = end_widget_session(request, payload.get("widget_session_id"))
    logger.info(
        "Sessao temporaria do widget encerrada. user_id=%s ended=%s",
        request.user.id,
        ended,
    )
    _safe_record_assistant_audit(
        user=request.user,
        origin=AssistantConversationOrigin.WIDGET,
        event_type=AUDIT_EVENT_WIDGET_SESSION_ENDED,
        input_text="Encerrar sessao temporaria do widget",
        final_response_status=AUDIT_STATUS_COMPLETED,
        response_text=(
            "Sessao temporaria encerrada."
            if ended
            else "Sessao temporaria nao encontrada ou ja encerrada."
        ),
    )
    return JsonResponse({"ended": ended})


@login_required
@require_POST
def assistant_widget_save_session_view(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    widget_session_id = payload.get("widget_session_id")
    try:
        conversation, already_saved = save_widget_session_as_conversation(
            request,
            request.user,
            widget_session_id,
        )
    except AssistantWidgetEmptySessionError:
        _safe_record_assistant_audit(
            user=request.user,
            origin=AssistantConversationOrigin.WIDGET,
            event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED,
            input_text="Salvar conversa do widget",
            block_reason=BLOCK_REASON_EMPTY_WIDGET_SESSION,
            final_response_status=AUDIT_STATUS_FAIL_SAFE,
            response_text="Nao ha mensagens para salvar nesta sessao.",
        )
        return JsonResponse({"detail": "Nao ha mensagens para salvar nesta sessao."}, status=400)
    except AssistantWidgetSessionError:
        _safe_record_assistant_audit(
            user=request.user,
            origin=AssistantConversationOrigin.WIDGET,
            event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED,
            input_text="Salvar conversa do widget",
            block_reason=BLOCK_REASON_INVALID_WIDGET_SESSION,
            final_response_status=AUDIT_STATUS_FAIL_SAFE,
            response_text="Invalid widget session.",
        )
        return JsonResponse({"detail": "Invalid widget session."}, status=400)
    except AssistantConversationLimitError as exc:
        _safe_record_assistant_audit(
            user=request.user,
            origin=AssistantConversationOrigin.WIDGET,
            event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED,
            input_text="Salvar conversa do widget",
            block_reason=BLOCK_REASON_CONVERSATION_LIMIT_REACHED,
            final_response_status=AUDIT_STATUS_BLOCKED_LIMIT,
            response_text=build_conversation_limit_response(exc.limit),
        )
        return JsonResponse(
            {"detail": build_conversation_limit_response(exc.limit)},
            status=409,
        )

    logger.info(
        "Sessao temporaria do widget salva como conversa persistida. conversation_id=%s user_id=%s already_saved=%s",
        conversation.id,
        request.user.id,
        already_saved,
    )
    _safe_record_assistant_audit(
        user=request.user,
        conversation=conversation,
        origin=AssistantConversationOrigin.WIDGET,
        event_type=AUDIT_EVENT_WIDGET_SESSION_SAVED,
        input_text="Salvar conversa do widget",
        final_response_status=AUDIT_STATUS_COMPLETED,
        response_text=(
            "Conversa do widget ja estava salva."
            if already_saved
            else "Conversa do widget salva com sucesso."
        ),
    )
    return JsonResponse(
        {
            "conversation_id": conversation.id,
            "already_saved": already_saved,
            "title": conversation.title,
        }
    )


@login_required
@require_GET
def assistant_conversation_view(request, conversation_id):
    conversation = AssistantConversation.objects.exclude(
        status=AssistantConversationStatus.DELETED,
    ).filter(pk=conversation_id).first()
    if conversation is None:
        raise Http404
    if not request.user.is_staff and conversation.created_by_id != request.user.id:
        raise Http404

    return JsonResponse(
        {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "origin": conversation.origin,
            "status": conversation.status,
            "messages": [
                _serialize_message(message)
                for message in conversation.messages.order_by("created_at", "id")
            ],
        }
    )
