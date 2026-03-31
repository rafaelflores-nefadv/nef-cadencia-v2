import os
from typing import TYPE_CHECKING

from apps.assistant.services.openai_settings import get_openai_settings

if TYPE_CHECKING:
    from openai import OpenAI


class OpenAIConfigError(Exception):
    pass


def get_openai_timeout_seconds() -> int:
    settings = get_openai_settings()
    timeout = int(settings["timeout_seconds"])
    return max(1, timeout)


def get_openai_client() -> "OpenAI":
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise OpenAIConfigError("OPENAI_API_KEY nao definido.")

    from openai import OpenAI

    return OpenAI(
        api_key=api_key,
        timeout=get_openai_timeout_seconds(),
    )
