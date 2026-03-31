from __future__ import annotations

import logging
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
from apps.assistant.services.business_rule_config import get_business_rule_definition
from apps.assistant.services.guardrails import normalize_user_text
from apps.assistant.services.analytics_context import get_productivity_context


SEMANTIC_CONTEXT_KEY = "semantic_operational"
SEMANTIC_ACTION_PREFIXES = ("envi", "mand", "notific", "avis", "dispar")
AGENT_LISTING_DEFAULT_LIMIT = 50
AGENT_LISTING_MAX_LIMIT = 50
PRODUCTIVITY_ANALYTICS_MAX_LIMIT = 20

logger = logging.getLogger("assistant")
TEMPORAL_TOOL_ARG_KEYS = ("date_from", "date_to", "year", "month", "period_key")


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
        "only_active": tool_args.get("only_active"),
        "search": tool_args.get("search"),
        "date_from": tool_args.get("date_from"),
        "date_to": tool_args.get("date_to"),
        "year": tool_args.get("year"),
        "month": tool_args.get("month"),
        "period_key": tool_args.get("period_key"),
    }
    return normalized


def resolve_semantic_operational_query(
    text: str,
    assistant_context: dict | None = None,
    *,
    allow_period_context_inheritance: bool = True,
) -> SemanticResolution:
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

    if _is_ambiguous_agents_productivity_question(normalized_text):
        ambiguity_tool_args = {
            "limit": ASSISTANT_ANALYTICS_DEFAULT_LIMIT,
            "group_by": "agent",
            "metric": "productivity",
            "ranking_order": "best",
        }
        return SemanticResolution(
            original_text=text,
            normalized_text=normalized_text,
            semantic_applied=True,
            intent="agent_productivity_ambiguity",
            expanded_text="consulta ambigua entre listagem de agentes e ranking de produtividade",
            tool_args=ambiguity_tool_args,
            subject="agent",
            metric="productivity",
            ranking_order="best",
            limit=ASSISTANT_ANALYTICS_DEFAULT_LIMIT,
            needs_clarification=True,
            clarification_response=_build_agents_productivity_ambiguity_response(),
            reason="ambiguous_agents_productivity_request",
        )

    matched_entry = _match_glossary_entry(normalized_text)
    if matched_entry is None:
        matched_entry = _infer_agent_listing_entry(normalized_text)
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
    limit = _resolve_limit(
        normalized_text,
        matched_entry,
        prior_context,
        current_intent=intent,
        explicit_limit=explicit_limit,
    )

    tool_args = _build_tool_args(
        intent=intent,
        metric=metric,
        ranking_order=ranking_order,
        subject=subject,
        limit=limit,
        normalized_text=normalized_text,
        explicit_period_args=explicit_period_args,
        prior_context=prior_context,
        allow_period_context_inheritance=allow_period_context_inheritance,
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
        configured_rule = get_business_rule_definition(business_rule or "")
        if configured_rule is not None:
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
                clarification_response=_build_business_rule_registered_response(
                    matched_entry.aliases[0],
                    configured_rule.summary,
                    configured_rule.criteria,
                    configured_rule.suggested_interpretation,
                ),
                matched_terms=matched_entry.aliases,
                reused_context=reused_context,
                context_applied_fields=context_fields,
                reason="business_rule_definition_loaded",
            )
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


def apply_semantic_resolution_to_tool_args(
    tool_name: str,
    tool_args: dict,
    semantic_resolution: SemanticResolution,
    *,
    allow_period_context_inheritance: bool = True,
) -> dict:
    merged_args = dict(tool_args or {})
    if not semantic_resolution.semantic_applied:
        return merged_args

    if tool_name == "get_productivity_analytics" and semantic_resolution.intent == "productivity_analytics_query":
        semantic_tool_args = semantic_resolution.tool_args or {}
        should_clear_temporal = _has_explicit_temporal_args(semantic_tool_args) or (
            not allow_period_context_inheritance
        )
        if should_clear_temporal:
            cleared_keys = [
                key
                for key in TEMPORAL_TOOL_ARG_KEYS
                if merged_args.pop(key, None) not in (None, "")
            ]
            if cleared_keys:
                logger.info(
                    "assistant.temporal_args_replaced intent=%s cleared_keys=%s allow_period_context_inheritance=%s",
                    semantic_resolution.intent,
                    ",".join(cleared_keys),
                    allow_period_context_inheritance,
                )
        for key, value in semantic_tool_args.items():
            if value in (None, ""):
                continue
            merged_args[key] = value
    if tool_name == "get_pause_ranking" and semantic_resolution.intent == "pause_ranking_query":
        for key, value in (semantic_resolution.tool_args or {}).items():
            if value in (None, ""):
                continue
            merged_args[key] = value
    if tool_name == "get_agents_listing" and semantic_resolution.intent == "agent_listing_query":
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
        re.search(
            r"\b(ranking|top|pior|piores|melhor|melhores|maior|maiores|menor|menores|mais|menos)\b",
            normalized_text,
        )
    )
    has_question_cue = bool(re.search(r"\b(quem|qual|quais)\b", normalized_text))
    has_request_cue = bool(re.search(r"\b(mostra|mostre|mostrar|liste|listar)\b", normalized_text))
    if not has_analytics_cue and not has_question_cue and not has_request_cue:
        return None

    if re.search(r"\bimprodutiv[a-z]*\b", normalized_text):
        metric = "improductivity"
        ranking_order = "worst"
    elif re.search(r"\bprodutiv[a-z]*\b", normalized_text):
        metric = "productivity"
        ranking_order = "best"
    elif re.search(r"\bproduz[a-z]*\b", normalized_text):
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


def _infer_agent_listing_entry(normalized_text: str) -> OperationalGlossaryEntry | None:
    has_agent_term = bool(re.search(r"\b(agente|agentes|operador|operadores)\b", normalized_text))
    if not has_agent_term:
        return None

    has_listing_verb = bool(
        re.search(r"\b(liste|listar|mostre|mostrar|quais|quem|existem|existem no sistema)\b", normalized_text)
    )
    has_listing_cue = bool(
        re.search(r"\b(cadastrad[a-z]*|existentes?|ativos?|sistema)\b", normalized_text)
    )
    is_generic_listing_question = bool(
        re.fullmatch(r"(liste|listar|mostre|mostrar)\s+(os\s+)?(agentes|operadores)", normalized_text)
        or re.fullmatch(r"(quais|quais sao)\s+(os\s+)?(agentes|operadores)", normalized_text)
    )
    has_analytics_cue = bool(
        re.search(
            r"\b(produtiv[a-z]*|improdutiv[a-z]*|desempenho|performance|ranking|top|melhor|pior|mais|menos)\b",
            normalized_text,
        )
    )
    has_other_operational_cue = bool(
        re.search(r"\b(pausa|pausas|resumo|sumario|dia|hoje|ontem)\b", normalized_text)
    )
    if not has_listing_verb:
        return None
    if has_other_operational_cue and not has_listing_cue:
        return None
    if has_analytics_cue and re.search(
        r"\b(produtiv[a-z]*|improdutiv[a-z]*|produtividade|improdutividade|desempenho|performance|ranking|top|mais|menos|melhor(?:es)?|pior(?:es)?|maior(?:es)?|menor(?:es)?)\b",
        normalized_text,
    ):
        return None
    if has_analytics_cue and not has_listing_cue:
        return None
    if not has_listing_cue and not is_generic_listing_question:
        return None

    only_active = bool(re.search(r"\b(ativos?|ativo)\b", normalized_text))
    return OperationalGlossaryEntry(
        key="direct_agent_listing_inference",
        category="agent_listing",
        aliases=(),
        intent="agent_listing_query",
        group_by="agent",
        default_limit=50,
        criteria=("only_active=true",) if only_active else (),
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

    current_moment_args = _match_current_moment_period_args(normalized_text)
    if current_moment_args:
        return current_moment_args

    broad_historical_args = _match_broad_historical_period_args(normalized_text)
    if broad_historical_args:
        return broad_historical_args

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


def _match_current_moment_period_args(normalized_text: str) -> dict:
    if "agora" in normalized_text and not re.search(
        (
            r"\b(hoje|today|neste momento|nesse momento|neste instante|nesse instante|"
            r"produtiv[a-z]*|improdutiv[a-z]*|desempenho|performance|"
            r"melhor(?:es)?|pior(?:es)?|pausa(?:s)?)\b"
        ),
        normalized_text,
    ):
        return {}
    if re.search(r"\b(hoje|today|agora|agora mesmo)\b", normalized_text):
        return {"period_key": "today"}
    if re.search(r"\b(neste|nesse)\s+momento\b", normalized_text):
        return {"period_key": "today"}
    if re.search(r"\b(neste|nesse)\s+instante\b", normalized_text):
        return {"period_key": "today"}
    return {}


def _match_broad_historical_period_args(normalized_text: str) -> dict:
    if re.search(
        (
            r"\b(de todos|no geral|geral|historico todo|historico completo|"
            r"todos os registros|desde sempre|desde o comeco|desde o inicio)\b"
        ),
        normalized_text,
    ):
        return {"period_key": "this_year"}
    return {}


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


def _can_inherit_limit(previous_intent: str | None, current_intent: str | None) -> bool:
    return bool(previous_intent and current_intent and previous_intent == current_intent)


def _can_inherit_only_active(previous_intent: str | None, current_intent: str | None) -> bool:
    return _can_inherit_limit(previous_intent, current_intent)


def _can_inherit_period(
    previous_intent: str | None,
    current_intent: str | None,
    *,
    allow_period_context_inheritance: bool,
) -> bool:
    if not allow_period_context_inheritance:
        return False
    return _can_inherit_limit(previous_intent, current_intent)


def _has_prior_temporal_context(prior_context: dict) -> bool:
    return any(
        prior_context.get(key) not in (None, "")
        for key in TEMPORAL_TOOL_ARG_KEYS
    )


def _sanitize_limit_for_intent(intent: str | None, raw_limit: int | None) -> int:
    default_limit = (
        AGENT_LISTING_DEFAULT_LIMIT
        if intent == "agent_listing_query"
        else ASSISTANT_ANALYTICS_DEFAULT_LIMIT
    )
    max_limit = (
        AGENT_LISTING_MAX_LIMIT
        if intent == "agent_listing_query"
        else PRODUCTIVITY_ANALYTICS_MAX_LIMIT
        if intent == "productivity_analytics_query"
        else 100
    )
    try:
        parsed_limit = int(raw_limit if raw_limit is not None else default_limit)
    except (TypeError, ValueError):
        parsed_limit = default_limit
    return max(1, min(parsed_limit, max_limit))


def _resolve_limit(
    normalized_text: str,
    matched_entry: OperationalGlossaryEntry | None,
    prior_context: dict,
    *,
    current_intent: str | None,
    explicit_limit: int | None = None,
) -> int:
    if explicit_limit is not None:
        return _sanitize_limit_for_intent(current_intent, explicit_limit)

    previous_intent = str(prior_context.get("intent") or "")
    if prior_context.get("limit"):
        if _can_inherit_limit(previous_intent, current_intent):
            inherited_limit = _sanitize_limit_for_intent(current_intent, prior_context.get("limit"))
            logger.info(
                "assistant.limit_inheritance_allowed previous_intent=%s current_intent=%s inherited_limit=%s applied_limit=%s",
                previous_intent,
                current_intent or "",
                prior_context.get("limit"),
                inherited_limit,
            )
            return inherited_limit
        logger.info(
            "assistant.limit_inheritance_blocked previous_intent=%s current_intent=%s previous_limit=%s",
            previous_intent,
            current_intent or "",
            prior_context.get("limit"),
        )

    if (
        re.search(r"\b(quem|qual)\b", normalized_text)
        and re.search(r"\b(pior|melhor)\b", normalized_text)
        and not re.search(r"\b(piores|melhores)\b", normalized_text)
    ):
        return _sanitize_limit_for_intent(current_intent, 1)
    if matched_entry is not None and matched_entry.default_limit:
        return _sanitize_limit_for_intent(current_intent, matched_entry.default_limit)
    return _sanitize_limit_for_intent(current_intent, None)


def _build_tool_args(
    *,
    intent: str | None,
    metric: str | None,
    ranking_order: str | None,
    subject: str | None,
    limit: int | None,
    normalized_text: str,
    explicit_period_args: dict,
    prior_context: dict,
    allow_period_context_inheritance: bool,
) -> dict:
    if intent == "agent_listing_query":
        previous_intent = str(prior_context.get("intent") or "")
        only_active = _has_only_active_constraint(normalized_text)
        if (
            not only_active
            and prior_context.get("only_active") is True
            and _can_inherit_only_active(previous_intent, intent)
        ):
            only_active = True
        tool_args = {
            "limit": _sanitize_limit_for_intent(intent, limit),
        }
        if only_active:
            tool_args["only_active"] = True
        return tool_args

    if intent == "productivity_analytics_query":
        previous_intent = str(prior_context.get("intent") or "")
        can_inherit_period = _can_inherit_period(
            previous_intent,
            intent,
            allow_period_context_inheritance=allow_period_context_inheritance,
        )
        if _has_prior_temporal_context(prior_context) and not explicit_period_args and not can_inherit_period:
            logger.info(
                "assistant.period_inheritance_blocked previous_intent=%s current_intent=%s allow_period_context_inheritance=%s",
                previous_intent,
                intent or "",
                allow_period_context_inheritance,
            )

        tool_args = {
            "metric": metric or prior_context.get("metric") or "improductivity",
            "ranking_order": ranking_order or prior_context.get("ranking_order") or "worst",
            "group_by": subject or prior_context.get("subject") or "agent",
            "limit": _sanitize_limit_for_intent(intent, limit),
        }
        only_active = _has_only_active_constraint(normalized_text)
        if (
            not only_active
            and prior_context.get("only_active") is True
            and _can_inherit_only_active(previous_intent, intent)
        ):
            only_active = True
        if only_active:
            tool_args["only_active"] = True
        if explicit_period_args:
            _clear_temporal_tool_args(tool_args)
            tool_args.update(explicit_period_args)
        elif can_inherit_period and prior_context.get("date_from") and prior_context.get("date_to"):
            tool_args["date_from"] = prior_context.get("date_from")
            tool_args["date_to"] = prior_context.get("date_to")
        elif can_inherit_period and prior_context.get("year") and prior_context.get("month"):
            tool_args["year"] = prior_context.get("year")
            tool_args["month"] = prior_context.get("month")
        elif can_inherit_period and prior_context.get("period_key"):
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


def _clear_temporal_tool_args(tool_args: dict) -> None:
    for key in TEMPORAL_TOOL_ARG_KEYS:
        tool_args.pop(key, None)


def _has_explicit_temporal_args(tool_args: dict) -> bool:
    return any(tool_args.get(key) not in (None, "") for key in TEMPORAL_TOOL_ARG_KEYS)


def _build_expanded_text(intent: str | None, tool_args: dict, business_rule: str | None) -> str:
    if intent == "agent_listing_query":
        if tool_args.get("only_active"):
            return (
                f"listagem de agentes ativos com limite "
                f"{tool_args.get('limit') or 50}"
            )
        return (
            f"listagem de agentes cadastrados com limite "
            f"{tool_args.get('limit') or 50}"
        )

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


def _build_business_rule_registered_response(
    term: str,
    summary: str,
    criteria: tuple[str, ...],
    suggested_interpretation: str | None,
) -> str:
    base = (
        f"Sou o {ASSISTANT_NAME}, {ASSISTANT_PLATFORM_ROLE}. "
        f"O termo '{term}' ja possui uma regra operacional cadastrada. "
        f"{summary}"
    )
    if criteria:
        base = f"{base} Criterios ativos: {'; '.join(criteria)}."
    if suggested_interpretation:
        return f"{base} Vou considerar essa interpretacao como referencia operacional."
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


def _has_only_active_constraint(normalized_text: str) -> bool:
    return bool(re.search(r"\b(ativo|ativos|ativa|ativas)\b", normalized_text))


def _is_combined_active_productivity_request(normalized_text: str) -> bool:
    has_active_signal = _has_only_active_constraint(normalized_text)
    has_productivity_signal = bool(
        re.search(
            r"\b(produtiv[a-z]*|improdutiv[a-z]*|produtividade|improdutividade|desempenho|performance)\b",
            normalized_text,
        )
    )
    if not (has_active_signal and has_productivity_signal):
        return False
    if re.search(r"\bou\b", normalized_text):
        return False
    if re.search(r"\btambem\b", normalized_text):
        return False
    if re.search(r"\bativos?\s+e\s+produtiv[a-z]*\b", normalized_text):
        return True
    if re.search(r"\b(agentes?|operadores?)\s+ativos?\s+mais\s+produtiv[a-z]*\b", normalized_text):
        return True
    if re.search(r"\branking\b.*\b(agentes?|operadores?)\s+ativos?\b.*\b(produtividade|produtiv[a-z]*)\b", normalized_text):
        return True
    if re.search(r"\bativos?\b.*\b(melhor(?:es)?|maior(?:es)?|ranking|produtividade|produtiv[a-z]*)\b", normalized_text):
        return True
    return False


def _has_explicit_dual_listing_analytics_request(normalized_text: str) -> bool:
    has_listing_signal = bool(
        re.search(
            r"\b(ativo|ativos|ativa|ativas|cadastrad[a-z]*|lista|listagem|existentes?|sistema)\b",
            normalized_text,
        )
    )
    has_analytics_signal = bool(
        re.search(
            r"\b(produtiv[a-z]*|improdutiv[a-z]*|produtividade|improdutividade|desempenho|performance|ranking)\b",
            normalized_text,
        )
    )
    if not (has_listing_signal and has_analytics_signal):
        return False
    if re.search(r"\bou\b", normalized_text):
        return True
    if re.search(r"\be\s+tambem\b", normalized_text):
        return True
    if re.search(r"\btambem\b.*\b(ranking|produtiv[a-z]*|produtividade|desempenho|performance)\b", normalized_text):
        return True
    if re.search(r"\b(ranking|produtiv[a-z]*|produtividade|desempenho|performance)\b.*\btambem\b", normalized_text):
        return True
    return False


def _is_ambiguous_agents_productivity_question(normalized_text: str) -> bool:
    if not re.search(r"\b(quais|quem|mostra|mostre|liste|listar|mostrar|quero|ver)\b", normalized_text):
        return False
    if not re.search(r"\b(agente|agentes|operador|operadores)\b", normalized_text):
        return False

    has_listing_signal = bool(
        re.search(
            r"\b(ativo|ativos|ativa|ativas|cadastrad[a-z]*|lista|listagem|existentes?|sistema)\b",
            normalized_text,
        )
    )
    has_analytics_signal = bool(
        re.search(
            r"\b(produtiv[a-z]*|improdutiv[a-z]*|produtividade|improdutividade|desempenho|performance|ranking)\b",
            normalized_text,
        )
    )
    if not (has_listing_signal and has_analytics_signal):
        return False

    if _has_explicit_dual_listing_analytics_request(normalized_text):
        return True
    if _is_combined_active_productivity_request(normalized_text):
        return False

    # Se a intencao analitica ja esta explicita, prioriza analytics.
    if re.search(
        r"\b(ranking|top|mais|menos|melhor(?:es)?|pior(?:es)?|maior(?:es)?|menor(?:es)?)\b",
        normalized_text,
    ):
        return False
    if re.search(r"\b(produtividade|improdutividade|desempenho|performance)\b", normalized_text):
        return False
    if re.search(r"\b(hoje|ontem|semana|mes|ano|periodo|data|entre)\b", normalized_text):
        return False
    if re.search(r"\b(maior|melhor)\s+produtiv[a-z]*\b", normalized_text):
        return False
    if re.search(r"\b(produtiv[a-z]*|improdutiv[a-z]*)\b.*\b(ranking|top)\b", normalized_text):
        return False

    return True


def _build_agents_productivity_ambiguity_response() -> str:
    return (
        f"Sou o {ASSISTANT_NAME}, {ASSISTANT_PLATFORM_ROLE}. "
        "Sua pergunta esta ambigua. Voce quer ver os agentes cadastrados/ativos "
        "ou um ranking de produtividade dos agentes?"
    )
