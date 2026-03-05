from django.urls import path

from .views import assistant_chat_view, assistant_conversation_view

urlpatterns = [
    path("chat", assistant_chat_view, name="assistant-chat"),
    path(
        "conversation/<int:conversation_id>",
        assistant_conversation_view,
        name="assistant-conversation",
    ),
]
