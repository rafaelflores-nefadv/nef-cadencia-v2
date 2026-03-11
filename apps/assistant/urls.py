from django.urls import path

from .views import (
    assistant_chat_view,
    assistant_conversation_view,
    assistant_page_conversation_detail_view,
    assistant_page_conversations_view,
    assistant_page_delete_conversation_view,
    assistant_page_view,
    assistant_widget_chat_view,
    assistant_widget_end_session_view,
    assistant_widget_save_session_view,
)

urlpatterns = [
    path("", assistant_page_view, name="assistant-page"),
    path("chat", assistant_chat_view, name="assistant-chat"),
    path(
        "conversations",
        assistant_page_conversations_view,
        name="assistant-page-conversations-api",
    ),
    path(
        "conversations/<int:conversation_id>",
        assistant_page_conversation_detail_view,
        name="assistant-page-conversation-api",
    ),
    path(
        "conversations/<int:conversation_id>/delete",
        assistant_page_delete_conversation_view,
        name="assistant-page-delete-conversation",
    ),
    path("widget/chat", assistant_widget_chat_view, name="assistant-widget-chat"),
    path(
        "widget/session/end",
        assistant_widget_end_session_view,
        name="assistant-widget-end-session",
    ),
    path(
        "widget/session/save",
        assistant_widget_save_session_view,
        name="assistant-widget-save-session",
    ),
    path(
        "conversation/<int:conversation_id>",
        assistant_conversation_view,
        name="assistant-conversation",
    ),
]
