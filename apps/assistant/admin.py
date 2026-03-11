from django.contrib import admin

from .models import (
    AssistantActionLog,
    AssistantAuditLog,
    AssistantConversation,
    AssistantMessage,
    AssistantUserPreference,
)


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "origin", "status", "is_persistent", "updated_at", "title")
    search_fields = ("id", "title", "created_by__username")
    list_filter = ("origin", "status", "is_persistent", "created_at")


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "created_at")
    search_fields = ("conversation__id", "content")
    list_filter = ("role", "created_at")


@admin.register(AssistantActionLog)
class AssistantActionLogAdmin(admin.ModelAdmin):
    list_display = ("tool_name", "requested_by", "status", "created_at", "conversation")
    search_fields = ("tool_name", "requested_by__username", "result_text")
    list_filter = ("status", "tool_name", "created_at")


@admin.register(AssistantAuditLog)
class AssistantAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "user",
        "conversation",
        "origin",
        "scope_classification",
        "capability_classification",
        "capability_id",
        "block_reason",
        "fallback_reason",
        "final_response_status",
        "created_at",
    )
    search_fields = (
        "input_text",
        "capability_id",
        "block_reason",
        "fallback_reason",
        "response_text",
    )
    list_filter = (
        "event_type",
        "origin",
        "scope_classification",
        "capability_classification",
        "final_response_status",
        "block_reason",
        "fallback_reason",
        "created_at",
    )
    ordering = ("-created_at", "-id")
    readonly_fields = (
        "conversation",
        "user",
        "origin",
        "event_type",
        "input_text",
        "scope_classification",
        "capability_classification",
        "capability_id",
        "tools_attempted_json",
        "tools_succeeded_json",
        "block_reason",
        "fallback_reason",
        "final_response_status",
        "response_text",
        "semantic_resolution_json",
        "pipeline_trace_json",
        "created_at",
    )


@admin.register(AssistantUserPreference)
class AssistantUserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "max_saved_conversations", "updated_at")
    search_fields = ("user__username",)
