from apps.rules.services.system_config import get_bool


ASSISTANT_SCOPE_GUARDRAIL_ENABLED_KEY = "ASSISTANT_SCOPE_GUARDRAIL_ENABLED"
ASSISTANT_CAPABILITY_GUARDRAIL_ENABLED_KEY = "ASSISTANT_CAPABILITY_GUARDRAIL_ENABLED"
ASSISTANT_OUTPUT_SCOPE_GUARDRAIL_ENABLED_KEY = "ASSISTANT_OUTPUT_SCOPE_GUARDRAIL_ENABLED"
ASSISTANT_OUTPUT_TRUTHFULNESS_GUARDRAIL_ENABLED_KEY = (
    "ASSISTANT_OUTPUT_TRUTHFULNESS_GUARDRAIL_ENABLED"
)


def is_scope_guardrail_enabled() -> bool:
    return get_bool(ASSISTANT_SCOPE_GUARDRAIL_ENABLED_KEY, default=True)


def is_capability_guardrail_enabled() -> bool:
    return get_bool(ASSISTANT_CAPABILITY_GUARDRAIL_ENABLED_KEY, default=True)


def is_output_scope_guardrail_enabled() -> bool:
    return get_bool(ASSISTANT_OUTPUT_SCOPE_GUARDRAIL_ENABLED_KEY, default=True)


def is_output_truthfulness_guardrail_enabled() -> bool:
    return get_bool(ASSISTANT_OUTPUT_TRUTHFULNESS_GUARDRAIL_ENABLED_KEY, default=True)
