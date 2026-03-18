"""
Selectors para queries do app assistant.
"""
from django.db.models import QuerySet, Count
from .models import (
    AssistantConversation,
    AssistantMessage,
    AssistantActionLog,
    AssistantAuditLog,
    AssistantConversationStatus,
)


def get_user_conversations(user, status=AssistantConversationStatus.ACTIVE) -> QuerySet:
    """
    Retorna conversas do usuário.
    
    Args:
        user: Usuário
        status: Status da conversa (opcional)
        
    Returns:
        QuerySet de AssistantConversation
    """
    qs = AssistantConversation.objects.filter(created_by=user)
    
    if status:
        qs = qs.filter(status=status)
    
    return qs.order_by('-updated_at')


def get_conversation_with_messages(conversation_id: int):
    """
    Retorna conversa com mensagens prefetchadas.
    
    Args:
        conversation_id: ID da conversa
        
    Returns:
        AssistantConversation ou None
    """
    return AssistantConversation.objects.prefetch_related('messages').filter(
        pk=conversation_id
    ).first()


def get_user_action_logs(user, limit=50) -> QuerySet:
    """
    Retorna logs de ações do usuário.
    
    Args:
        user: Usuário
        limit: Número máximo de resultados
        
    Returns:
        QuerySet de AssistantActionLog
    """
    return AssistantActionLog.objects.filter(
        requested_by=user
    ).order_by('-created_at')[:limit]


def get_user_audit_logs(user, limit=100) -> QuerySet:
    """
    Retorna logs de auditoria do usuário.
    
    Args:
        user: Usuário
        limit: Número máximo de resultados
        
    Returns:
        QuerySet de AssistantAuditLog
    """
    return AssistantAuditLog.objects.filter(
        user=user
    ).order_by('-created_at')[:limit]


def get_conversation_messages(conversation_id: int) -> QuerySet:
    """
    Retorna mensagens de uma conversa.
    
    Args:
        conversation_id: ID da conversa
        
    Returns:
        QuerySet de AssistantMessage
    """
    return AssistantMessage.objects.filter(
        conversation_id=conversation_id
    ).order_by('created_at')
