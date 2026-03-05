from django.conf import settings
from django.db import models


class AssistantMessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class AssistantConversation(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, blank=True, default="")

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} message in conversation #{self.conversation_id}"


class AssistantActionLogStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"
    DENIED = "denied", "Denied"


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
        choices=AssistantActionLogStatus.choices,
    )
    result_text = models.TextField(blank=True, default="")
    result_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.tool_name} ({self.status})"
