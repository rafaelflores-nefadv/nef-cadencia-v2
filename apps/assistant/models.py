from django.conf import settings
from django.db import models

from apps.assistant.observability import (
    AUDIT_EVENT_CHAT_MESSAGE,
    AUDIT_EVENT_CHOICES,
    AUDIT_EVENT_CONVERSATION_DELETED,
    AUDIT_EVENT_PAGE_CONVERSATION_CREATED,
    AUDIT_EVENT_WIDGET_SESSION_ENDED,
    AUDIT_EVENT_WIDGET_SESSION_SAVED,
    AUDIT_STATUS_CHOICES,
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
    INTERACTION_ORIGIN_CHOICES,
    INTERACTION_ORIGIN_PAGE,
    INTERACTION_ORIGIN_WIDGET,
    TOOL_EXECUTION_RESULT_CHOICES,
    TOOL_EXECUTION_RESULT_DENIED,
    TOOL_EXECUTION_RESULT_ERROR,
    TOOL_EXECUTION_RESULT_SUCCESS,
)
from apps.assistant.services.assistant_config import (
    ASSISTANT_DEFAULT_CONVERSATION_LIMIT,
    ASSISTANT_DEFAULT_CONVERSATION_TITLE,
)


class AssistantConversationOrigin(models.TextChoices):
    WIDGET = INTERACTION_ORIGIN_WIDGET, "Widget"
    PAGE = INTERACTION_ORIGIN_PAGE, "Page"


class AssistantConversationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    DELETED = "deleted", "Deleted"


class AssistantMessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class AssistantConversation(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    origin = models.CharField(
        max_length=20,
        choices=AssistantConversationOrigin.choices,
        default=AssistantConversationOrigin.WIDGET,
    )
    status = models.CharField(
        max_length=20,
        choices=AssistantConversationStatus.choices,
        default=AssistantConversationStatus.ACTIVE,
    )
    is_persistent = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(
        max_length=200,
        blank=True,
        default=ASSISTANT_DEFAULT_CONVERSATION_TITLE,
    )
    context_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return f"Conversation #{self.id}"


class AssistantMessage(models.Model):
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=AssistantMessageRole.choices)
    content = models.TextField()
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role} message in conversation #{self.conversation_id}"


class AssistantActionLogStatus(models.TextChoices):
    SUCCESS = TOOL_EXECUTION_RESULT_SUCCESS, "Success"
    ERROR = TOOL_EXECUTION_RESULT_ERROR, "Error"
    DENIED = TOOL_EXECUTION_RESULT_DENIED, "Denied"


class AssistantActionLog(models.Model):
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_logs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_action_logs",
    )
    tool_name = models.CharField(max_length=100)
    tool_args_json = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=TOOL_EXECUTION_RESULT_CHOICES,
    )
    result_text = models.TextField(blank=True, default="")
    result_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.tool_name} ({self.status})"


class AssistantAuditLogStatus(models.TextChoices):
    COMPLETED = AUDIT_STATUS_COMPLETED, "Completed"
    BLOCKED_SCOPE = AUDIT_STATUS_BLOCKED_SCOPE, "Blocked scope"
    BLOCKED_CAPABILITY = AUDIT_STATUS_BLOCKED_CAPABILITY, "Blocked capability"
    BLOCKED_LIMIT = AUDIT_STATUS_BLOCKED_LIMIT, "Blocked limit"
    NO_DATA = AUDIT_STATUS_NO_DATA, "No data"
    DISABLED = AUDIT_STATUS_DISABLED, "Disabled"
    CONFIG_ERROR = AUDIT_STATUS_CONFIG_ERROR, "Config error"
    TOOL_FAILURE = AUDIT_STATUS_TOOL_FAILURE, "Tool failure"
    TEMPORARY_FAILURE = AUDIT_STATUS_TEMPORARY_FAILURE, "Temporary failure"
    FAIL_SAFE = AUDIT_STATUS_FAIL_SAFE, "Fail-safe"


class AssistantAuditEventType(models.TextChoices):
    CHAT_MESSAGE = AUDIT_EVENT_CHAT_MESSAGE, "Chat message"
    PAGE_CONVERSATION_CREATED = (
        AUDIT_EVENT_PAGE_CONVERSATION_CREATED,
        "Page conversation created",
    )
    WIDGET_SESSION_SAVED = AUDIT_EVENT_WIDGET_SESSION_SAVED, "Widget session saved"
    WIDGET_SESSION_ENDED = AUDIT_EVENT_WIDGET_SESSION_ENDED, "Widget session ended"
    CONVERSATION_DELETED = AUDIT_EVENT_CONVERSATION_DELETED, "Conversation deleted"


class AssistantAuditLog(models.Model):
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assistant_audit_logs",
    )
    origin = models.CharField(
        max_length=20,
        choices=INTERACTION_ORIGIN_CHOICES,
        default=INTERACTION_ORIGIN_WIDGET,
    )
    event_type = models.CharField(
        max_length=40,
        choices=AUDIT_EVENT_CHOICES,
        default=AUDIT_EVENT_CHAT_MESSAGE,
    )
    input_text = models.TextField()
    scope_classification = models.CharField(max_length=40, blank=True, default="")
    capability_classification = models.CharField(max_length=40, blank=True, default="")
    capability_id = models.CharField(max_length=100, blank=True, default="")
    tools_attempted_json = models.JSONField(default=list)
    tools_succeeded_json = models.JSONField(default=list)
    block_reason = models.CharField(max_length=100, blank=True, default="")
    fallback_reason = models.CharField(max_length=100, blank=True, default="")
    final_response_status = models.CharField(
        max_length=40,
        choices=AUDIT_STATUS_CHOICES,
        default=AUDIT_STATUS_COMPLETED,
    )
    response_text = models.TextField(blank=True, default="")
    semantic_resolution_json = models.JSONField(default=dict, blank=True)
    pipeline_trace_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Audit #{self.id} ({self.final_response_status})"


class AssistantUserPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_user_preference",
    )
    max_saved_conversations = models.PositiveIntegerField(
        default=ASSISTANT_DEFAULT_CONVERSATION_LIMIT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self):
        return f"Assistant preferences for user #{self.user_id}"
