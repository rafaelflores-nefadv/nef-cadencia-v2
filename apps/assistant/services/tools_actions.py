import json
import urllib.error
import urllib.request
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template import Context, Template
from django.utils import timezone

from apps.integrations.models import Integration
from apps.messaging.choices import ChannelChoices, TemplateTypeChoices
from apps.messaging.models import MessageTemplate
from apps.monitoring.models import Agent, NotificationHistory, NotificationStatusChoices
from apps.rules.services.system_config import get_int, get_json

User = get_user_model()

INTERNAL_CHAT_ALIASES = {"internal_chat", "chatseguro"}
DEFAULT_ALLOWED_TEMPLATES = ["pause_warning", "pause_overflow", "supervisor_alert"]
TEMPLATE_KEY_TO_TYPE = {
    "pause_warning": TemplateTypeChoices.SEM_PAUSA,
    "pause_overflow": TemplateTypeChoices.MUITAS_PAUSAS,
    "supervisor_alert": TemplateTypeChoices.SUPERVISOR_ALERTA,
}
SUPPORTED_CHANNELS = {
    ChannelChoices.CHATSEGURO,
    ChannelChoices.EMAIL,
    ChannelChoices.WEBHOOK,
    ChannelChoices.SLACK,
    ChannelChoices.TEAMS,
}


def _normalize_channel(channel: str | None) -> str:
    normalized = (channel or "").strip().lower()
    if normalized in INTERNAL_CHAT_ALIASES:
        return ChannelChoices.CHATSEGURO
    return normalized


def _allowed_template_keys() -> set[str]:
    raw = get_json("ASSISTANT_ALLOWED_TEMPLATES_JSON", default=DEFAULT_ALLOWED_TEMPLATES)
    if not isinstance(raw, list):
        raw = DEFAULT_ALLOWED_TEMPLATES
    normalized = {
        str(item).strip().lower()
        for item in raw
        if str(item).strip()
    }
    return normalized or set(DEFAULT_ALLOWED_TEMPLATES)


def _template_type_for_key(template_key: str) -> str:
    key = template_key.strip().lower()
    if key in TEMPLATE_KEY_TO_TYPE:
        return TEMPLATE_KEY_TO_TYPE[key]
    valid_template_types = {choice[0] for choice in TemplateTypeChoices.choices}
    if key in valid_template_types:
        return key
    return TemplateTypeChoices.NOTIFICACAO_GENERICA


def _find_template(template_key: str, channel: str):
    template_type = _template_type_for_key(template_key)
    return (
        MessageTemplate.objects
        .filter(active=True, channel=channel, template_type=template_type)
        .order_by("-version", "-updated_at")
        .first()
    )


def _render_template_text(template_text: str, variables: dict) -> str:
    template_obj = Template(template_text or "")
    context = Context(variables or {})
    return template_obj.render(context).strip()


def _throttle_window_minutes() -> int:
    return max(1, get_int("NOTIFY_THROTTLE_MINUTES", default=30))


def _is_throttled(notification_type: str, recipient: str) -> bool:
    window_start = timezone.now() - timedelta(minutes=_throttle_window_minutes())
    return NotificationHistory.objects.filter(
        notification_type=notification_type,
        recipient=recipient,
        created_at__gte=window_start,
        status=NotificationStatusChoices.SENT,
    ).exists()


def _get_integration(channel: str):
    return (
        Integration.objects
        .filter(channel=channel, enabled=True)
        .order_by("-updated_at", "-id")
        .first()
    )


def _create_notification_history(
    *,
    agent: Agent | None,
    notification_type: str,
    channel: str,
    recipient: str,
    template: MessageTemplate | None,
    status: str,
    payload: dict,
    error_message: str = "",
):
    return NotificationHistory.objects.create(
        agent=agent,
        cd_operador=agent.cd_operador if agent else None,
        notification_type=notification_type,
        channel=channel,
        recipient=recipient,
        template=template,
        status=status,
        error_message=error_message[:1000] if error_message else "",
        payload=payload,
    )


def _dispatch_email(subject: str, body: str, recipient: str, integration: Integration):
    config = integration.config_json if isinstance(integration.config_json, dict) else {}
    from_email = config.get("from_email")
    if not from_email or "@" not in recipient:
        return {"status": "skipped", "reason": "queued_email_missing_sender_or_recipient"}

    send_mail(
        subject=subject or "Notificacao operacional",
        message=body,
        from_email=from_email,
        recipient_list=[recipient],
        fail_silently=False,
    )
    return {"status": "success", "reason": "email_sent"}


def _dispatch_webhook(payload: dict, integration: Integration):
    config = integration.config_json if isinstance(integration.config_json, dict) else {}
    url = (config.get("url") or "").strip()
    if not url:
        return {"status": "skipped", "reason": "queued_webhook_missing_url"}

    request = urllib.request.Request(
        url=url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    timeout_seconds = int(config.get("timeout_seconds", 10))
    with urllib.request.urlopen(request, timeout=max(1, timeout_seconds)) as response:
        code = getattr(response, "status", 200)
        if code >= 400:
            raise urllib.error.HTTPError(url, code, "HTTP error", hdrs=None, fp=None)

    return {"status": "success", "reason": "webhook_sent"}


def _dispatch_notification(
    *,
    agent: Agent | None,
    template: MessageTemplate,
    channel: str,
    recipient: str,
    rendered_subject: str,
    rendered_body: str,
    variables: dict,
):
    integration = _get_integration(channel)
    payload = {
        "subject": rendered_subject,
        "body": rendered_body,
        "variables": variables or {},
        "template_name": template.name,
        "template_type": template.template_type,
    }

    if integration is None:
        history = _create_notification_history(
            agent=agent,
            notification_type=template.template_type,
            channel=channel,
            recipient=recipient,
            template=template,
            status=NotificationStatusChoices.SKIPPED,
            payload=payload,
            error_message="queued_integration_not_configured",
        )
        return {
            "status": "skipped",
            "reason": "queued_integration_not_configured",
            "notification_history_id": history.id,
        }

    try:
        if channel == ChannelChoices.CHATSEGURO:
            dispatch = {"status": "success", "reason": "internal_chat_stub_sent"}
        elif channel == ChannelChoices.EMAIL:
            dispatch = _dispatch_email(rendered_subject, rendered_body, recipient, integration)
        elif channel == ChannelChoices.WEBHOOK:
            dispatch = _dispatch_webhook(
                {
                    "recipient": recipient,
                    "message": payload,
                    "agent_id": agent.id if agent else None,
                },
                integration,
            )
        else:
            dispatch = {"status": "skipped", "reason": "queued_channel_not_implemented"}
    except Exception as exc:
        history = _create_notification_history(
            agent=agent,
            notification_type=template.template_type,
            channel=channel,
            recipient=recipient,
            template=template,
            status=NotificationStatusChoices.ERROR,
            payload=payload,
            error_message=str(exc),
        )
        return {
            "status": "error",
            "reason": "dispatch_failed",
            "detail": str(exc),
            "notification_history_id": history.id,
        }

    if dispatch["status"] == "success":
        history_status = NotificationStatusChoices.SENT
    else:
        history_status = NotificationStatusChoices.SKIPPED

    history = _create_notification_history(
        agent=agent,
        notification_type=template.template_type,
        channel=channel,
        recipient=recipient,
        template=template,
        status=history_status,
        payload=payload,
        error_message=dispatch.get("reason", ""),
    )
    return {
        "status": dispatch["status"],
        "reason": dispatch.get("reason", ""),
        "notification_history_id": history.id,
    }


def send_message_to_agent(
    *,
    user,
    agent_id: int,
    template_key: str,
    channel: str,
    variables: dict | None = None,
) -> dict:
    if not getattr(user, "is_staff", False):
        return {"status": "denied", "reason": "Sem permissao"}

    normalized_channel = _normalize_channel(channel)
    if normalized_channel not in SUPPORTED_CHANNELS:
        return {"status": "error", "reason": "Canal nao suportado"}

    key = (template_key or "").strip().lower()
    if key not in _allowed_template_keys():
        return {"status": "denied", "reason": "template_key nao permitido"}

    try:
        agent = Agent.objects.get(pk=int(agent_id))
    except (TypeError, ValueError, Agent.DoesNotExist):
        return {"status": "error", "reason": "Agente nao encontrado"}

    template = _find_template(key, normalized_channel)
    if template is None:
        return {"status": "error", "reason": "Template nao encontrado"}

    recipient = agent.email if normalized_channel == ChannelChoices.EMAIL else f"agent:{agent.id}"
    if _is_throttled(template.template_type, recipient):
        history = _create_notification_history(
            agent=agent,
            notification_type=template.template_type,
            channel=normalized_channel,
            recipient=recipient,
            template=template,
            status=NotificationStatusChoices.SKIPPED,
            payload={"variables": variables or {}, "template_key": key},
            error_message="throttled",
        )
        return {
            "status": "skipped",
            "reason": "throttled",
            "notification_history_id": history.id,
        }

    rendered_subject = _render_template_text(template.subject or "", variables or {})
    rendered_body = _render_template_text(template.body or "", variables or {})
    dispatch = _dispatch_notification(
        agent=agent,
        template=template,
        channel=normalized_channel,
        recipient=recipient,
        rendered_subject=rendered_subject,
        rendered_body=rendered_body,
        variables=variables or {},
    )
    dispatch.update(
        {
            "agent_id": agent.id,
            "agent_name": agent.nm_agente or "",
            "template_key": key,
            "channel": normalized_channel,
        }
    )
    return dispatch


def _supervisor_recipients(channel: str):
    supervisors = User.objects.filter(is_staff=True, is_active=True).order_by("id")
    recipients = []
    for user in supervisors:
        if channel == ChannelChoices.EMAIL:
            recipient = (user.email or "").strip()
            if not recipient:
                recipient = f"user:{user.id}"
        else:
            recipient = f"user:{user.id}"
        recipients.append((user, recipient))
    return recipients


def notify_supervisors(
    *,
    user,
    template_key: str,
    channel: str,
    variables: dict | None = None,
) -> dict:
    if not getattr(user, "is_staff", False):
        return {"status": "denied", "reason": "Sem permissao"}

    normalized_channel = _normalize_channel(channel)
    if normalized_channel not in SUPPORTED_CHANNELS:
        return {"status": "error", "reason": "Canal nao suportado"}

    key = (template_key or "").strip().lower()
    if key not in _allowed_template_keys():
        return {"status": "denied", "reason": "template_key nao permitido"}

    template = _find_template(key, normalized_channel)
    if template is None:
        return {"status": "error", "reason": "Template nao encontrado"}

    rendered_subject = _render_template_text(template.subject or "", variables or {})
    rendered_body = _render_template_text(template.body or "", variables or {})
    recipients = _supervisor_recipients(normalized_channel)

    sent_count = 0
    skipped_count = 0
    error_count = 0
    item_results = []

    for supervisor, recipient in recipients:
        if _is_throttled(template.template_type, recipient):
            history = _create_notification_history(
                agent=None,
                notification_type=template.template_type,
                channel=normalized_channel,
                recipient=recipient,
                template=template,
                status=NotificationStatusChoices.SKIPPED,
                payload={"variables": variables or {}, "template_key": key, "user_id": supervisor.id},
                error_message="throttled",
            )
            skipped_count += 1
            item_results.append(
                {
                    "recipient": recipient,
                    "user_id": supervisor.id,
                    "status": "skipped",
                    "notification_history_id": history.id,
                }
            )
            continue

        dispatch = _dispatch_notification(
            agent=None,
            template=template,
            channel=normalized_channel,
            recipient=recipient,
            rendered_subject=rendered_subject,
            rendered_body=rendered_body,
            variables={**(variables or {}), "supervisor_username": supervisor.username},
        )
        if dispatch["status"] == "success":
            sent_count += 1
        elif dispatch["status"] == "skipped":
            skipped_count += 1
        else:
            error_count += 1

        item_results.append(
            {
                "recipient": recipient,
                "user_id": supervisor.id,
                "status": dispatch["status"],
                "notification_history_id": dispatch.get("notification_history_id"),
            }
        )

    overall_status = "success"
    if sent_count == 0 and skipped_count > 0 and error_count == 0:
        overall_status = "skipped"
    if error_count > 0 and sent_count == 0:
        overall_status = "error"

    return {
        "status": overall_status,
        "template_key": key,
        "channel": normalized_channel,
        "total_supervisors": len(recipients),
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "results": item_results,
        "scope": "all_staff_users_mvp",
    }
