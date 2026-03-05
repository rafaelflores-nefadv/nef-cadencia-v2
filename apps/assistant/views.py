import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import AssistantConversation
from .services.assistant_service import run_chat


def _parse_json_body(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


@login_required
@require_POST
def assistant_chat_view(request):
    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"detail": "Field 'text' is required."}, status=400)

    result = run_chat(
        user=request.user,
        text=text,
        conversation_id=payload.get("conversation_id"),
    )
    return JsonResponse(result)


@login_required
@require_GET
def assistant_conversation_view(request, conversation_id):
    conversation = AssistantConversation.objects.filter(pk=conversation_id).first()
    if conversation is None:
        raise Http404
    if not request.user.is_staff and conversation.created_by_id != request.user.id:
        raise Http404

    messages = (
        conversation.messages
        .order_by("created_at", "id")
        .values("role", "content", "created_at")
    )
    return JsonResponse(
        {
            "conversation_id": conversation.id,
            "messages": [
                {
                    "role": message["role"],
                    "content": message["content"],
                    "created_at": message["created_at"].isoformat(),
                }
                for message in messages
            ],
        }
    )
