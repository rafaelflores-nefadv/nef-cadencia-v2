from apps.rules.services.system_config import get_bool, get_config, get_float, get_int

DEFAULT_OPENAI_ENABLED = True
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_TEMPERATURE = 0.2
DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = 600
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30


def get_openai_settings() -> dict:
    return {
        "enabled": get_bool("OPENAI_ENABLED", default=DEFAULT_OPENAI_ENABLED),
        "model": get_config("OPENAI_MODEL", default=DEFAULT_OPENAI_MODEL),
        "temperature": get_float("OPENAI_TEMPERATURE", default=DEFAULT_OPENAI_TEMPERATURE),
        "max_output_tokens": get_int(
            "OPENAI_MAX_OUTPUT_TOKENS",
            default=DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
        ),
        "timeout_seconds": get_int(
            "OPENAI_TIMEOUT_SECONDS",
            default=DEFAULT_OPENAI_TIMEOUT_SECONDS,
        ),
    }
