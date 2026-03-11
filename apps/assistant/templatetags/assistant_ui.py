import json

from django import template

from apps.assistant.services.assistant_config import (
    ASSISTANT_NAME,
    ASSISTANT_SCOPE_TOPICS,
)
from apps.assistant.services.processing_status import build_processing_ui_config


register = template.Library()


@register.simple_tag
def assistant_name() -> str:
    return ASSISTANT_NAME


@register.simple_tag
def assistant_empty_message() -> str:
    return f"Pergunte ao {ASSISTANT_NAME} sobre {ASSISTANT_SCOPE_TOPICS}."


@register.simple_tag
def assistant_input_placeholder() -> str:
    return "Pergunte sobre dados e funcionalidades da plataforma"


@register.simple_tag
def assistant_save_conversation_label() -> str:
    return "Salvar conversa"


@register.simple_tag
def assistant_saved_conversation_label() -> str:
    return "Conversa salva"


@register.simple_tag
def assistant_processing_config_json() -> str:
    return json.dumps(build_processing_ui_config(), ensure_ascii=False)
