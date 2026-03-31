from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import (
    AssistantActionLog,
    AssistantAuditLog,
    AssistantConversation,
    AssistantMessage,
    AssistantUserPreference,
)


def delete_selected_conversations(modeladmin, request, queryset):
    """Ação customizada para excluir conversas selecionadas"""
    count = queryset.count()
    user_counts = {}
    
    for conversation in queryset:
        username = conversation.created_by.username if conversation.created_by else "Sem usuário"
        user_counts[username] = user_counts.get(username, 0) + 1
    
    queryset.delete()
    
    details = ", ".join([f"{count} de {user}" for user, count in user_counts.items()])
    messages.success(
        request,
        f"{count} conversa(s) excluída(s) com sucesso: {details}"
    )

delete_selected_conversations.short_description = "🗑️ Excluir conversas selecionadas"


def delete_user_conversations(modeladmin, request, queryset):
    """Excluir TODAS as conversas dos usuários selecionados"""
    users = set(conv.created_by for conv in queryset if conv.created_by)
    
    if not users:
        messages.warning(request, "Nenhum usuário encontrado nas conversas selecionadas")
        return
    
    total_deleted = 0
    for user in users:
        user_conversations = AssistantConversation.objects.filter(created_by=user)
        count = user_conversations.count()
        user_conversations.delete()
        total_deleted += count
        messages.info(request, f"Excluídas {count} conversas de {user.username}")
    
    messages.success(request, f"Total: {total_deleted} conversas excluídas de {len(users)} usuário(s)")

delete_user_conversations.short_description = "🗑️ Excluir TODAS conversas dos usuários selecionados"


def delete_old_conversations(modeladmin, request, queryset):
    """Excluir conversas com mais de 30 dias"""
    from datetime import timedelta
    from django.utils import timezone
    
    cutoff_date = timezone.now() - timedelta(days=30)
    old_conversations = queryset.filter(updated_at__lt=cutoff_date)
    count = old_conversations.count()
    
    if count == 0:
        messages.info(request, "Nenhuma conversa com mais de 30 dias encontrada")
        return
    
    user_counts = {}
    for conversation in old_conversations:
        username = conversation.created_by.username if conversation.created_by else "Sem usuário"
        user_counts[username] = user_counts.get(username, 0) + 1
    
    old_conversations.delete()
    
    details = ", ".join([f"{count} de {user}" for user, count in user_counts.items()])
    messages.success(
        request,
        f"{count} conversa(s) antiga(s) excluída(s): {details}"
    )

delete_old_conversations.short_description = "🧹 Limpar conversas antigas (>30 dias)"


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "origin", "status", "is_persistent", "message_count_display", "updated_at", "title")
    search_fields = ("id", "title", "created_by__username")
    list_filter = ("origin", "status", "is_persistent", "created_at")
    actions = [delete_selected_conversations, delete_user_conversations, delete_old_conversations]
    date_hierarchy = "created_at"
    
    def message_count_display(self, obj):
        """Mostrar quantidade de mensagens"""
        count = obj.messages.count()
        if count == 0:
            return format_html('<span style="color: #999;">0 msgs</span>')
        elif count < 5:
            return format_html('<span style="color: #0066cc;">{} msgs</span>', count)
        else:
            return format_html('<span style="color: #00aa00; font-weight: bold;">{} msgs</span>', count)
    
    message_count_display.short_description = "Mensagens"


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
