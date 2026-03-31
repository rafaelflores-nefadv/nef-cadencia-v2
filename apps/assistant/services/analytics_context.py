from __future__ import annotations

from copy import deepcopy


PRODUCTIVITY_ANALYTICS_CONTEXT_KEY = "productivity_analytics"
PRODUCTIVITY_PERIOD_KEYS = ("date_from", "date_to", "year", "month", "period_key")
PRODUCTIVITY_PARAM_KEYS = (
    "metric",
    "group_by",
    "ranking_order",
    "limit",
)


def normalize_assistant_context(raw_context) -> dict:
    if not isinstance(raw_context, dict):
        return {}
    return deepcopy(raw_context)


def get_productivity_context(raw_context) -> dict | None:
    normalized = normalize_assistant_context(raw_context)
    value = normalized.get(PRODUCTIVITY_ANALYTICS_CONTEXT_KEY)
    if not isinstance(value, dict):
        return None
    start_date = str(value.get("start_date") or "").strip()
    end_date = str(value.get("end_date") or "").strip()
    if not start_date or not end_date:
        return None
    return {
        "start_date": start_date,
        "end_date": end_date,
        "metric": str(value.get("metric") or "").strip().lower() or None,
        "group_by": str(value.get("group_by") or "").strip().lower() or None,
        "ranking_order": str(value.get("ranking_order") or "").strip().lower() or None,
        "limit": _coerce_positive_int(value.get("limit")),
    }


def build_productivity_context(tool_args: dict, tool_result: dict) -> dict | None:
    if not isinstance(tool_result, dict):
        return None

    start_date = str(tool_result.get("date_from") or "").strip()
    end_date = str(tool_result.get("date_to") or "").strip()
    if not start_date or not end_date:
        return None

    tool_args = tool_args if isinstance(tool_args, dict) else {}
    return {
        "start_date": start_date,
        "end_date": end_date,
        "metric": str(tool_result.get("metric") or tool_args.get("metric") or "").strip().lower() or None,
        "group_by": str(tool_result.get("group_by") or tool_args.get("group_by") or "").strip().lower() or None,
        "ranking_order": str(
            tool_result.get("ranking_order") or tool_args.get("ranking_order") or ""
        ).strip().lower() or None,
        "limit": _coerce_positive_int(tool_result.get("limit") or tool_args.get("limit")),
    }


def merge_productivity_context(raw_context, productivity_context: dict | None) -> dict:
    normalized = normalize_assistant_context(raw_context)
    if not isinstance(productivity_context, dict):
        return normalized
    normalized[PRODUCTIVITY_ANALYTICS_CONTEXT_KEY] = productivity_context
    return normalized


def apply_productivity_context_to_tool_args(
    tool_args: dict,
    raw_context,
    *,
    allow_period_inheritance: bool = True,
) -> tuple[dict, bool]:
    merged_args = dict(tool_args or {})
    productivity_context = get_productivity_context(raw_context)
    if productivity_context is None:
        return merged_args, False

    reused_context = False
    explicit_period = any(merged_args.get(key) not in (None, "") for key in PRODUCTIVITY_PERIOD_KEYS)
    if allow_period_inheritance and not explicit_period:
        merged_args["date_from"] = productivity_context["start_date"]
        merged_args["date_to"] = productivity_context["end_date"]
        reused_context = True

    for key in PRODUCTIVITY_PARAM_KEYS:
        context_value = (
            productivity_context["start_date"]
            if key == "date_from"
            else productivity_context["end_date"]
            if key == "date_to"
            else productivity_context.get(key)
        )
        if key in merged_args and merged_args.get(key) not in (None, ""):
            continue
        if context_value in (None, ""):
            continue
        merged_args[key] = context_value

    return merged_args, reused_context


def format_productivity_context_instruction(
    raw_context,
    *,
    allow_period_inheritance: bool = True,
) -> str | None:
    if not allow_period_inheritance:
        return None

    productivity_context = get_productivity_context(raw_context)
    if productivity_context is None:
        return None

    return (
        "Contexto validado da ultima consulta analitica desta conversa: "
        f"periodo de {productivity_context['start_date']} ate {productivity_context['end_date']}; "
        f"metrica={productivity_context.get('metric') or 'indefinida'}; "
        f"agrupamento={productivity_context.get('group_by') or 'indefinido'}; "
        f"ordenacao={productivity_context.get('ranking_order') or 'indefinida'}; "
        f"limite={productivity_context.get('limit') or 'indefinido'}. "
        "Se a nova pergunta nao explicitar outro periodo, reutilize esse periodo anterior."
    )


def _coerce_positive_int(value) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed
