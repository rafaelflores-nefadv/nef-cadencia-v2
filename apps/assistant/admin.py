from django.contrib import admin

from .models import AssistantActionLog, AssistantConversation, AssistantMessage


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "created_at", "title")
    search_fields = ("id", "title", "created_by__username")
    list_filter = ("created_at",)


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
