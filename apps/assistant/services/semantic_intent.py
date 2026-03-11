from dataclasses import dataclass

from apps.assistant.services.semantic_resolution import (
    apply_semantic_resolution_to_tool_args,
    format_semantic_resolution_instruction,
    resolve_semantic_operational_query,
)


@dataclass(frozen=True)
class SemanticIntent:
    capability_id: str | None = None
    tool_args: dict | None = None
    expanded_text: str = ""
    reason: str = ""


def normalize_semantic_intent(text: str, assistant_context: dict | None = None) -> SemanticIntent:
    resolution = resolve_semantic_operational_query(text, assistant_context)
    return SemanticIntent(
        capability_id=resolution.intent,
        tool_args=resolution.tool_args or {},
        expanded_text=resolution.expanded_text,
        reason=resolution.reason,
    )


def apply_semantic_intent_to_tool_args(tool_name: str, tool_args: dict, semantic_intent: SemanticIntent) -> dict:
    class _IntentAdapter:
        semantic_applied = bool(semantic_intent.capability_id)
        intent = semantic_intent.capability_id
        tool_args = semantic_intent.tool_args or {}

    return apply_semantic_resolution_to_tool_args(tool_name, tool_args, _IntentAdapter())


def format_semantic_intent_instruction(semantic_intent: SemanticIntent) -> str | None:
    class _IntentAdapter:
        semantic_applied = bool(semantic_intent.capability_id)
        intent = semantic_intent.capability_id
        business_rule = None
        metric = (semantic_intent.tool_args or {}).get("metric")
        subject = (semantic_intent.tool_args or {}).get("group_by")
        ranking_order = (semantic_intent.tool_args or {}).get("ranking_order")
        limit = (semantic_intent.tool_args or {}).get("limit")
        reused_context = False
        needs_clarification = False
        needs_business_definition = False

    return format_semantic_resolution_instruction(_IntentAdapter())
