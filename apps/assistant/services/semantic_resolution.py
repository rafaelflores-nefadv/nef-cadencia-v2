from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.assistant.services.assistant_config import (
    ASSISTANT_ANALYTICS_DEFAULT_LIMIT,
    ASSISTANT_ANALYTICS_GROUP_ALIASES,
    ASSISTANT_ANALYTICS_MONTH_ALIASES,
    ASSISTANT_ANALYTICS_PERIOD_KEYWORDS,
    ASSISTANT_NAME,
    ASSISTANT_PLATFORM_ROLE,
    ASSISTANT_EXTERNAL_CONTEXT_PREFIXES,
    ASSISTANT_OUT_OF_SCOPE_TERMS,
)
from apps.assistant.services.business_glossary import (
    OPERATIONAL_GLOSSARY,
    OperationalGlossaryEntry,
)
from apps.assistant.services.guardrails import normalize_user_text
from apps.assistant.services.analytics_context import get_productivity_context


SEMANTIC_CONTEXT_KEY = "semantic_operational"
SEMANTIC_ACTION_PREFIXES = ("envi", "mand", "notific", "avis", "dispar")


@dataclass(frozen=True)
class SemanticResolution:
    original_text: str
    normalized_text: str
    semantic_applied: bool = False
    intent: str | None = None
    expanded_text: str = ""
    tool_args: dict | None = None
    business_rule: str | None = None
    subject: str | None = None
    metric: str | None = None
    ranking_order: str | None = None
    limit: int | None = None
    needs_clarification: bool = False
    needs_business_definition: bool = False
    clarification_response: str | None = None
    matched_terms: tuple[str, ...] = ()
    reused_context: bool = False
    context_applied_fields: tuple[str, ...] = ()
    reason: str = ""

    def to_audit_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "semantic_applied": self.semantic_applied,
            "intent": self.intent,
            "expanded_text": self.expanded_text,
            "tool_args": self.tool_args or {},
            "business_rule": self.business_rule,
            "subject": self.subject,
            "metric": self.metric,
            "ranking_order": self.ranking_order,
            "limit": self.limit,
            "needs_clarification": self.needs_clarification,
            "needs_business_definition": self.needs_business_definition,
            "clarification_response": self.clarification_response,
            "matched_terms": list(self.matched_terms),
            "reused_context": self.reused_context,
            "context_applied_fields": list(self.context_applied_fields),
            "reason": self.reason,
        }


def get_semantic_context(raw_context) -> dict | None:
    if not isinstance(raw_context, dict):
        return None
    legacy_context = get_productivity_context(raw_context)
    value = raw_context.get(SEMANTIC_CONTEXT_KEY)
    if isinstance(value, dict):
        semantic_context = dict(value)
        if legacy_context is not None:
            fallbacks = {
                "subject": legacy_context.get("group_by"),
                "metric": legacy_context.get("metric"),
                "ranking_order": legacy_context.get("ranking_order"),
                "limit": legacy_context.get("limit"),
                "date_from": legacy_context.get("start_date"),
                "date_to": legacy_context.get("end_date"),
            }
            for key, fallback_value in fallbacks.items():
                if semantic_context.get(key) in (None, "") and fallback_value not in (None, ""):
                    semantic_context[key] = fallback_value
        return semantic_context

    if legacy_context is None:
        return None
    return {
        "intent": "productivity_analytics_query",
        "subject": legacy_context.get("group_by"),
        "metric": legacy_context.get("metric"),
        "ranking_order": legacy_context.get("ranking_order"),
        "limit": legacy_context.get("limit"),
        "date_from": legacy_context.get("start_date"),
        "date_to": legacy_context.get("end_date"),
    }


def merge_semantic_context(raw_context, semantic_resolution: SemanticResolution | None) -> dict:
    normalized = dict(raw_context or {}) if isinstance(raw_context, dict) else {}
    if semantic_resolution is None or not semantic_resolution.semantic_applied:
        return normalized

    tool_args = semantic_resolution.tool_args or {}
    normalized[SEMANTIC_CONTEXT_KEY] = {
        "intent": semantic_resolution.intent,
        "subject": semantic_resolution.subject,
        "metric": semantic_resolution.metric,
        "ranking_order": semantic_resolution.ranking_order,
        "limit": semantic_resolution.limit,
        "business_rule": semantic_resolution.business_rule,
        "date_from": tool_args.get("date_from"),
        "date_to": tool_args.get("date_to"),
        "year": tool_args.get("year"),
        "month": tool_args.get("month"),
        "period_key": tool_args.get("period_key"),
    }
    return normalized


def resolve_semantic_operational_query(text: str, assistant_context: dict | None = None) -> SemanticResolution:
    normalized_text = normalize_user_text(text)
    if not normalized_text:
        return SemanticResolution(original_text=text, normalized_text=normalized_text)

    if any(term in normalized_text for term in ASSISTANT_OUT_OF_SCOPE_TERMS):
        return SemanticResolution(original_text=text, normalized_text=normalized_text)
    if any(prefix in normalized_text for prefix in ASSISTANT_EXTERNAL_CONTEXT_PREFIXES):
        return SemanticResolution(original_text=text, normalized_text=normalized_text)

    prior_context = get_semantic_context(assistant_context or {}) or {}
    explicit_period_args = _match_period_args(normalized_text)
    explicit_group = _match_group_by(normalized_text)
    explicit_limit = _match_limit(normalized_text)

    matched_entry = _match_glossary_entry(normalized_text)
    if matched_entry is None:
        matched_entry = _infer_direct_analytics_entry(normalized_text)
    if matched_entry is not None and _contains_explicit_action_request(normalized_text):
        if matched_entry.intent in {"productivity_analytics_query", "pause_ranking_query"}:
            matched_entry = None
    if matched_entry is None and not _looks_like_follow_up(normalized_text, prior_context):
        return SemanticResolution(original_text=text, normalized_text=normalized_text)

    intent = matched_entry.intent if matched_entry is not None else prior_context.get("intent")
    business_rule = matched_entry.business_rule if matched_entry is not None else prior_context.get("business_rule")
    subject = explicit_group or (matched_entry.group_by if matched_entry is not None else None) or prior_context.get("subject") or "agent"
    metric = (matched_entry.metric if matched_entry is not None else None) or prior_context.get("metric")
    ranking_order = _resolve_ranking_order(normalized_text, matched_entry, prior_context)
    limit = explicit_limit or _resolve_limit(normalized_text, matched_entry, prior_context)

    tool_args = _build_tool_args(
        intent=intent,
        metric=metric,
        ranking_order=ranking_order,
        subject=subject,
        limit=limit,
        explicit_period_args=explicit_period_args,
        prior_context=prior_context,
    )
    reused_context, context_fields = _detect_context_reuse(explicit_period_args, tool_args, prior_context)

    if matched_entry and matched_entry.needs_clarification:
        return SemanticResolution(
            original_text=text,
            normalized_text=normalized_text,
            semantic_applied=True,
            intent=intent,
            expanded_text=_build_expanded_text(intent, tool_args, business_rule),
            tool_args=tool_args,
            business_rule=business_rule,
            subject=subject,
            metric=metric,
            ranking_order=ranking_order,
            limit=limit,
            needs_clarification=True,
            clarification_response=_build_ambiguous_term_response(
                matched_entry.aliases[0],
                matched_entry.clarification_hint or "o criterio operacional correto",
            ),
            matched_terms=matched_entry.aliases,
            reused_context=reused_context,
            context_applied_fields=context_fields,
            reason="ambiguous_operational_term",
        )

    if matched_entry and matched_entry.requires_business_definition:
        return SemanticResolution(
            original_text=text,
            normalized_text=normalized_text,
            semantic_applied=True,
            intent=intent,
            expanded_text=_build_expanded_text(intent, tool_args, business_rule),
            tool_args=tool_args,
            business_rule=business_rule,
            subject=subject,
            metric=metric,
            ranking_order=ranking_order,
            limit=limit,
            needs_business_definition=True,
            clarification_response=_build_business_rule_definition_response(
                matched_entry.aliases[0],
                matched_entry.suggested_interpretation,
            ),
            matched_terms=matched_entry.aliases,
            reused_context=reused_context,
            context_applied_fields=context_fields,
            reason="business_rule_definition_required",
        )

    if intent is None:
        return SemanticResolution(original_text=text, normalized_text=normalized_text)

    return SemanticResolution(
        original_text=text,
        normalized_text=normalized_text,
        semantic_applied=True,
        intent=intent,
        expanded_text=_build_expanded_text(intent, tool_args, business_rule),
        tool_args=tool_args,
        business_rule=business_rule,
        subject=subject,
        metric=metric,
        ranking_order=ranking_order,
        limit=limit,
        matched_terms=matched_entry.aliases if matched_entry is not None else (),
        reused_context=reused_context,
        context_applied_fields=context_fields,
        reason="semantic_glossary_match" if matched_entry is not None else "semantic_follow_up",
    )


def apply_semantic_resolution_to_tool_args(tool_name: str, tool_args: dict, semantic_resolution: SemanticResolution) -> dict:
    merged_args = dict(tool_args or {})
    if not semantic_resolution.semantic_applied:
        return merged_args

    if tool_name == "get_productivity_analytics" and semantic_resolution.intent == "productivity_analytics_query":
        for key, value in (semantic_resolution.tool_args or {}).items():
            if value in (None, ""):
                continue
            merged_args[key] = value
    if tool_name == "get_pause_ranking" and semantic_resolution.intent == "pause_ranking_query":
        for key, value in (semantic_resolution.tool_args or {}).items():
            if value in (None, ""):
                continue
            merged_args[key] = value
    return merged_args


def format_semantic_resolution_instruction(semantic_resolution: SemanticResolution) -> str | None:
    if not semantic_resolution.semantic_applied:
        return None
    return (
        "Resolucao semantica operacional: "
        f"intent={semantic_resolution.intent or ''}; "
        f"business_rule={semantic_resolution.business_rule or ''}; "
        f"metric={semantic_resolution.metric or ''}; "
        f"subject={semantic_resolution.subject or ''}; "
        f"ranking_order={semantic_resolution.ranking_order or ''}; "
        f"limit={semantic_resolution.limit or ''}; "
        f"reused_context={semantic_resolution.reused_context}; "
        f"needs_clarification={semantic_resolution.needs_clarification}; "
        f"needs_business_definition={semantic_resolution.needs_business_definition}."
    )


def _match_glossary_entry(normalized_text: str) -> OperationalGlossaryEntry | None:
    best_entry = None
    best_alias_length = -1
    for entry in OPERATIONAL_GLOSSARY:
        for alias in entry.aliases:
            if alias in normalized_text and len(alias) > best_alias_length:
                best_entry = entry
                best_alias_length = len(alias)
    return best_entry


def _infer_direct_analytics_entry(normalized_text: str) -> OperationalGlossaryEntry | None:
    has_analytics_cue = bool(
        re.search(r"\b(ranking|top|pior|piores|melhor|melhores)\b", normalized_text)
    )
    has_question_cue = bool(re.search(r"\b(quem|qual|quais)\b", normalized_text))
    if not has_analytics_cue and not has_question_cue:
        return None

    if re.search(r"\bimprodutiv[a-z]*\b", normalized_text):
        metric = "improductivity"
        ranking_order = "worst"
    elif re.search(r"\bprodutiv[a-z]*\b", normalized_text):
        metric = "productivity"
        ranking_order = "best"
    elif re.search(r"\b(desempenho|performance)\b", normalized_text):
        metric = "performance"
        ranking_order = "worst"
    else:
        return None

    return OperationalGlossaryEntry(
        key="direct_analytics_inference",
        category="direct_analytics",
        aliases=(),
        intent="productivity_analytics_query",
        metric=metric,
        ranking_order=ranking_order,
        group_by="agent",
        default_limit=ASSISTANT_ANALYTICS_DEFAULT_LIMIT,
    )


def _match_group_by(normalized_text: str) -> str | None:
    for group_by, aliases in ASSISTANT_ANALYTICS_GROUP_ALIASES:
        if any(alias in normalized_text for alias in aliases):
            return group_by
    return None


def _match_limit(normalized_text: str) -> int | None:
    top_match = re.search(r"\btop\s+(\d{1,2})\b", normalized_text)
    if top_match:
        return int(top_match.group(1))
    count_match = re.search(r"\b(?:os|as)?\s*(\d{1,2})\s+(?:piores|melhores)\b", normalized_text)
    if count_match:
        return int(count_match.group(1))
    comparative_match = re.search(
        r"\b(?:os|as)?\s*(\d{1,2})\s+(?:(?:agentes?|operadores?|equipes?)\s+)?"
        r"(?:mais|menos)\s+(?:produtiv[a-z]*|improdutiv[a-z]*)\b",
        normalized_text,
    )
    if comparative_match:
        return int(comparative_match.group(1))
    if re.search(r"\b(quem|qual)\b.*\b(pior|melhor)\b", normalized_text):
        return 1
    return None


def _match_period_args(normalized_text: str) -> dict:
    month_match = re.search(
        r"\b("
        + "|".join(ASSISTANT_ANALYTICS_MONTH_ALIASES.keys())
        + r")\b(?:\s+de)?\s+(\d{4})",
        normalized_text,
    )
    if month_match:
        return {
            "year": int(month_match.group(2)),
            "month": ASSISTANT_ANALYTICS_MONTH_ALIASES[month_match.group(1)],
        }

    month_without_year_match = re.search(
        r"\b(" + "|".join(ASSISTANT_ANALYTICS_MONTH_ALIASES.keys()) + r")\b",
        normalized_text,
    )
    if month_without_year_match:
        today = timezone.localdate()
        return {
            "year": today.year,
            "month": ASSISTANT_ANALYTICS_MONTH_ALIASES[month_without_year_match.group(1)],
        }

    natural_period_args = _match_natural_period_args(normalized_text)
    if natural_period_args:
        return natural_period_args

    for period_key, aliases in ASSISTANT_ANALYTICS_PERIOD_KEYWORDS:
        if any(alias in normalized_text for alias in aliases):
            return {"period_key": period_key}
    return {}


def _match_natural_period_args(normalized_text: str) -> dict:
    today = timezone.localdate()
    current_year_start = today.replace(month=1, day=1)
    current_month_start = today.replace(day=1)
    current_week_start = today - timedelta(days=today.weekday())

    if _is_year_to_date_phrase(normalized_text):
        return {
            "date_from": current_year_start.isoformat(),
            "date_to": today.isoformat(),
        }

    if _is_month_to_date_phrase(normalized_text):
        return {
            "date_from": current_month_start.isoformat(),
            "date_to": today.isoformat(),
        }

    if _is_week_to_date_phrase(normalized_text):
        return {
            "date_from": current_week_start.isoformat(),
            "date_to": today.isoformat(),
        }

    return {}


def _is_year_to_date_phrase(normalized_text: str) -> bool:
    return bool(
        re.search(r"\b(?:do|esse|neste|no)\s+ano\b", normalized_text)
        or re.search(r"\b(?:pior|melhor|ranking)\b.*\bdo ano\b", normalized_text)
        or re.search(r"\bquem\s+foi\s+pior\b.*\bno ano\b", normalized_text)
        or re.search(r"\bquem\s+esta\b.*\besse ano\b", normalized_text)
    )


def _is_month_to_date_phrase(normalized_text: str) -> bool:
    return bool(
        re.search(r"\b(?:este|nesse|neste)\s+mes\b", normalized_text)
        or re.search(r"\bate agora no mes\b", normalized_text)
        or re.search(r"\b(?:do|no)\s+mes\b(?!\s+passado)(?!\s+que vem)", normalized_text)
    )


def _is_week_to_date_phrase(normalized_text: str) -> bool:
    return bool(
        re.search(r"\b(?:essa|nesta)\s+semana\b", normalized_text)
        or re.search(r"\bate agora na semana\b", normalized_text)
        or re.search(r"\bna semana\b(?!\s+passada)(?!\s+que vem)", normalized_text)
    )


def _resolve_ranking_order(
    normalized_text: str,
    matched_entry: OperationalGlossaryEntry | None,
    prior_context: dict,
) -> str | None:
    explicit_order = _resolve_explicit_metric_order(normalized_text)
    if explicit_order:
        return explicit_order
    if "melhor" in normalized_text or "melhores" in normalized_text:
        return "best"
    if "pior" in normalized_text or "piores" in normalized_text:
        return "worst"
    if matched_entry is not None and matched_entry.ranking_order:
        return matched_entry.ranking_order
    return prior_context.get("ranking_order")


def _resolve_limit(normalized_text: str, matched_entry: OperationalGlossaryEntry | None, prior_context: dict) -> int:
    explicit = _match_limit(normalized_text)
    if explicit is not None:
        return explicit
    if prior_context.get("limit"):
        return int(prior_context["limit"])
    if (
        re.search(r"\b(quem|qual)\b", normalized_text)
        and re.search(r"\b(pior|melhor)\b", normalized_text)
        and not re.search(r"\b(piores|melhores)\b", normalized_text)
    ):
        return 1
    if matched_entry is not None and matched_entry.default_limit:
        return matched_entry.default_limit
    return int(prior_context.get("limit") or ASSISTANT_ANALYTICS_DEFAULT_LIMIT)


def _build_tool_args(
    *,
    intent: str | None,
    metric: str | None,
    ranking_order: str | None,
    subject: str | None,
    limit: int | None,
    explicit_period_args: dict,
    prior_context: dict,
) -> dict:
    if intent == "productivity_analytics_query":
        tool_args = {
            "metric": metric or prior_context.get("metric") or "improductivity",
            "ranking_order": ranking_order or prior_context.get("ranking_order") or "worst",
            "group_by": subject or prior_context.get("subject") or "agent",
            "limit": limit or int(prior_context.get("limit") or ASSISTANT_ANALYTICS_DEFAULT_LIMIT),
        }
        if explicit_period_args:
            tool_args.update(explicit_period_args)
        elif prior_context.get("date_from") and prior_context.get("date_to"):
            tool_args["date_from"] = prior_context.get("date_from")
            tool_args["date_to"] = prior_context.get("date_to")
        elif prior_context.get("year") and prior_context.get("month"):
            tool_args["year"] = prior_context.get("year")
            tool_args["month"] = prior_context.get("month")
        elif prior_context.get("period_key"):
            tool_args["period_key"] = prior_context.get("period_key")
        return tool_args

    if intent == "pause_ranking_query":
        tool_args = {"limit": limit or ASSISTANT_ANALYTICS_DEFAULT_LIMIT}
        if explicit_period_args.get("period_key") == "today":
            tool_args["date"] = timezone.localdate().isoformat()
        elif explicit_period_args.get("period_key") == "yesterday":
            tool_args["date"] = (timezone.localdate() - timedelta(days=1)).isoformat()
        elif prior_context.get("date_from") == prior_context.get("date_to") and prior_context.get("date_from"):
            tool_args["date"] = prior_context.get("date_from")
        else:
            tool_args["date"] = timezone.localdate().isoformat()
        return tool_args

    return explicit_period_args


def _looks_like_follow_up(normalized_text: str, prior_context: dict) -> bool:
    if not prior_context:
        return False
    shorthand_terms = (
        "e os melhores",
        "e os piores",
        "top",
        "melhores",
        "piores",
        "agora o top",
        "no mes passado",
        "esse mes",
        "os 5 piores",
        "os 10 piores",
        "os 5 melhores",
        "os 10 melhores",
    )
    if any(term in normalized_text for term in shorthand_terms):
        return True
    return bool(re.fullmatch(r"(e\s+)?(os\s+)?(melhores|piores)\??", normalized_text))


def _contains_explicit_action_request(normalized_text: str) -> bool:
    tokens = normalized_text.split()
    return any(token.startswith(prefix) for token in tokens for prefix in SEMANTIC_ACTION_PREFIXES)


def _detect_context_reuse(explicit_period_args: dict, tool_args: dict, prior_context: dict) -> tuple[bool, tuple[str, ...]]:
    applied = []
    if prior_context and not explicit_period_args:
        if tool_args.get("date_from") and tool_args.get("date_to"):
            applied.extend(["date_from", "date_to"])
        elif tool_args.get("year") and tool_args.get("month"):
            applied.extend(["year", "month"])
        elif tool_args.get("period_key"):
            applied.append("period_key")
    for field in ("metric", "group_by", "ranking_order", "limit"):
        prior_key = "subject" if field == "group_by" else field
        if (
            field in tool_args
            and field not in explicit_period_args
            and prior_context.get(prior_key) == tool_args.get(field)
        ):
            applied.append(field)
    applied_tuple = tuple(sorted(set(applied)))
    return bool(applied_tuple), applied_tuple


def _build_expanded_text(intent: str | None, tool_args: dict, business_rule: str | None) -> str:
    if intent == "productivity_analytics_query":
        group_label = "agentes" if tool_args.get("group_by") != "team" else "equipes"
        metric_label = {
            "improductivity": "improdutividade",
            "productivity": "produtividade",
            "performance": "desempenho",
        }.get(tool_args.get("metric"), "desempenho")
        polarity = "melhores" if tool_args.get("ranking_order") == "best" else "piores"
        period = _build_period_phrase(tool_args)
        return (
            f"ranking de {metric_label} dos {group_label} {polarity}{period} "
            f"com limite {tool_args.get('limit') or ASSISTANT_ANALYTICS_DEFAULT_LIMIT}"
        ).strip()
    if intent == "pause_ranking_query":
        date_ref = tool_args.get("date") or timezone.localdate().isoformat()
        return f"ranking de pausas dos agentes na data {date_ref} com limite {tool_args.get('limit') or ASSISTANT_ANALYTICS_DEFAULT_LIMIT}"
    if intent == "business_rule_query":
        period = _build_period_phrase(tool_args)
        return f"consulta da regra operacional {business_rule or 'indefinida'} para agentes{period}".strip()
    if intent == "clarification_query":
        period = _build_period_phrase(tool_args)
        return f"consulta de criterio operacional para agentes{period}".strip()
    return ""


def _build_period_phrase(tool_args: dict) -> str:
    if tool_args.get("date_from") and tool_args.get("date_to"):
        return f" no periodo de {tool_args['date_from']} ate {tool_args['date_to']}"
    if tool_args.get("year") and tool_args.get("month"):
        return f" em {int(tool_args['month']):02d}/{tool_args['year']}"
    if tool_args.get("period_key"):
        return f" no periodo {tool_args['period_key']}"
    return ""


def _build_business_rule_definition_response(term: str, suggested_interpretation: str | None) -> str:
    base = (
        f"Sou o {ASSISTANT_NAME}, {ASSISTANT_PLATFORM_ROLE}. "
        f"Entendi o termo '{term}', mas ainda preciso de uma regra operacional cadastrada "
        "para responder isso com seguranca."
    )
    if suggested_interpretation:
        return f"{base} Posso interpretar isso como {suggested_interpretation}?"
    return base


def _build_ambiguous_term_response(term: str, clarification_hint: str) -> str:
    return (
        f"Sou o {ASSISTANT_NAME}, {ASSISTANT_PLATFORM_ROLE}. "
        f"O termo '{term}' esta ambiguo no contexto operacional. "
        f"Voce quer dizer {clarification_hint}?"
    )


def _resolve_explicit_metric_order(normalized_text: str) -> str | None:
    if re.search(r"\bmais\s+produtiv[a-z]*\b", normalized_text):
        return "best"
    if re.search(r"\bmenos\s+produtiv[a-z]*\b", normalized_text):
        return "worst"
    if re.search(r"\bmais\s+improdutiv[a-z]*\b", normalized_text):
        return "worst"
    if re.search(r"\bmenos\s+improdutiv[a-z]*\b", normalized_text):
        return "best"
    return None
