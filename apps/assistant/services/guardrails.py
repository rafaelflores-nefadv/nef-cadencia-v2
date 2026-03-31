import re
import unicodedata
from dataclasses import dataclass

from apps.assistant.services.assistant_config import (
    ASSISTANT_ANALYTICAL_CONTEXT_PREFIXES,
    ASSISTANT_BYPASS_TERMS,
    ASSISTANT_EXTERNAL_CONTEXT_PREFIXES,
    ASSISTANT_OPERATIONAL_ENTITY_PREFIXES,
    ASSISTANT_OPERATIONAL_METRIC_PREFIXES,
    ASSISTANT_OUT_OF_SCOPE_TERMS,
    ASSISTANT_OUTPUT_CONFIRMATION_PREFIXES,
    ASSISTANT_OUTPUT_CONTEXT_REQUEST_PREFIXES,
    ASSISTANT_OUTPUT_SYSTEM_USAGE_PREFIXES,
    ASSISTANT_OUTPUT_STATUS_PREFIXES,
    ASSISTANT_PLATFORM_CONTEXT_PREFIXES,
    ASSISTANT_QUERY_CUE_PREFIXES,
    ASSISTANT_SAFE_FALLBACK_RESPONSE,
    ASSISTANT_SCOPE_ALLOWED_PATTERNS,
    ASSISTANT_STRICT_OPERATIONAL_METRIC_PREFIXES,
    ASSISTANT_STRONG_DOMAIN_PREFIXES,
    ASSISTANT_WEAK_DOMAIN_PREFIXES,
    ASSISTANT_OPERATIONAL_INTENT_PREFIXES,
    ASSISTANT_OPERATIONAL_TIME_PREFIXES,
)


DENTRO_DO_ESCOPO = "DENTRO_DO_ESCOPO"
FORA_DO_ESCOPO = "FORA_DO_ESCOPO"


@dataclass(frozen=True)
class ScopeSignals:
    normalized_text: str
    tokens: tuple[str, ...]
    strong_domain_matches: tuple[str, ...] = ()
    weak_domain_matches: tuple[str, ...] = ()
    entity_matches: tuple[str, ...] = ()
    metric_matches: tuple[str, ...] = ()
    analytical_matches: tuple[str, ...] = ()
    platform_matches: tuple[str, ...] = ()
    intent_matches: tuple[str, ...] = ()
    query_matches: tuple[str, ...] = ()
    time_matches: tuple[str, ...] = ()
    output_confirmation_matches: tuple[str, ...] = ()
    output_status_matches: tuple[str, ...] = ()
    output_context_request_matches: tuple[str, ...] = ()
    pattern_matches: tuple[str, ...] = ()
    external_matches: tuple[str, ...] = ()
    bypass_matches: tuple[str, ...] = ()
    out_of_scope_matches: tuple[str, ...] = ()

    @property
    def domain_match_count(self) -> int:
        return len(self.strong_domain_matches) + len(self.weak_domain_matches)

    @property
    def strict_metric_matches(self) -> tuple[str, ...]:
        return tuple(
            match
            for match in self.metric_matches
            if match in ASSISTANT_STRICT_OPERATIONAL_METRIC_PREFIXES
        )

    @property
    def has_analytical_or_time_context(self) -> bool:
        return bool(self.analytical_matches or self.time_matches or self.pattern_matches)

    @property
    def has_operational_scope(self) -> bool:
        return bool(
            self.strong_domain_matches
            or self.weak_domain_matches
            or self.entity_matches
            or self.metric_matches
            or self.platform_matches
            or self.pattern_matches
        )

    @property
    def platform_family_count(self) -> int:
        families = [
            bool(
                self.strong_domain_matches
                or self.weak_domain_matches
                or self.entity_matches
                or self.metric_matches
            ),
            bool(self.platform_matches),
            bool(
                self.intent_matches
                or self.query_matches
                or self.pattern_matches
                or self.analytical_matches
            ),
            bool(self.time_matches),
        ]
        return sum(1 for item in families if item)


@dataclass(frozen=True)
class ScopeValidationResult:
    classification: str
    response: str | None = None
    reason: str = ""
    matched_terms: tuple[str, ...] = ()


def blocked_result(reason: str, matched_terms: tuple[str, ...] = ()) -> ScopeValidationResult:
    return ScopeValidationResult(
        classification=FORA_DO_ESCOPO,
        response=ASSISTANT_SAFE_FALLBACK_RESPONSE,
        reason=reason,
        matched_terms=matched_terms,
    )


def normalize_user_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    collapsed = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", collapsed).strip()


def _tokenize(normalized_text: str) -> tuple[str, ...]:
    if not normalized_text:
        return ()
    return tuple(token for token in normalized_text.split(" ") if token)


def _find_phrase_matches(normalized_text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(term for term in terms if term in normalized_text)


def _find_prefix_matches(tokens: tuple[str, ...], prefixes: tuple[str, ...]) -> tuple[str, ...]:
    matches = []
    for prefix in prefixes:
        if any(token.startswith(prefix) for token in tokens):
            matches.append(prefix)
    return tuple(matches)


def _find_pattern_matches(normalized_text: str) -> tuple[str, ...]:
    matches = []
    for pattern in ASSISTANT_SCOPE_ALLOWED_PATTERNS:
        if re.search(pattern, normalized_text):
            matches.append(pattern)
    return tuple(matches)


def analyze_text(text: str) -> ScopeSignals:
    normalized_text = normalize_user_text(text)
    tokens = _tokenize(normalized_text)
    return ScopeSignals(
        normalized_text=normalized_text,
        tokens=tokens,
        strong_domain_matches=_find_prefix_matches(tokens, ASSISTANT_STRONG_DOMAIN_PREFIXES),
        weak_domain_matches=_find_prefix_matches(tokens, ASSISTANT_WEAK_DOMAIN_PREFIXES),
        entity_matches=_find_prefix_matches(tokens, ASSISTANT_OPERATIONAL_ENTITY_PREFIXES),
        metric_matches=_find_prefix_matches(tokens, ASSISTANT_OPERATIONAL_METRIC_PREFIXES),
        analytical_matches=_find_prefix_matches(tokens, ASSISTANT_ANALYTICAL_CONTEXT_PREFIXES),
        platform_matches=_find_prefix_matches(tokens, ASSISTANT_PLATFORM_CONTEXT_PREFIXES),
        intent_matches=_find_prefix_matches(tokens, ASSISTANT_OPERATIONAL_INTENT_PREFIXES),
        query_matches=_find_prefix_matches(tokens, ASSISTANT_QUERY_CUE_PREFIXES),
        time_matches=_find_prefix_matches(tokens, ASSISTANT_OPERATIONAL_TIME_PREFIXES),
        output_confirmation_matches=_find_prefix_matches(
            tokens,
            ASSISTANT_OUTPUT_CONFIRMATION_PREFIXES,
        ),
        output_status_matches=_find_prefix_matches(tokens, ASSISTANT_OUTPUT_STATUS_PREFIXES),
        output_context_request_matches=_find_prefix_matches(
            tokens,
            ASSISTANT_OUTPUT_CONTEXT_REQUEST_PREFIXES,
        ),
        pattern_matches=_find_pattern_matches(normalized_text),
        external_matches=_find_prefix_matches(tokens, ASSISTANT_EXTERNAL_CONTEXT_PREFIXES),
        bypass_matches=_find_phrase_matches(normalized_text, ASSISTANT_BYPASS_TERMS),
        out_of_scope_matches=_find_phrase_matches(normalized_text, ASSISTANT_OUT_OF_SCOPE_TERMS),
    )


def classify_scope(text: str) -> ScopeValidationResult:
    signals = analyze_text(text)
    if not signals.normalized_text:
        return blocked_result("empty_text")

    if signals.bypass_matches:
        return blocked_result("prompt_injection", signals.bypass_matches)

    if signals.out_of_scope_matches:
        return blocked_result("out_of_scope_phrase", signals.out_of_scope_matches)

    if len(signals.external_matches) >= 2:
        return blocked_result("external_context", signals.external_matches)

    if (
        signals.external_matches
        and signals.platform_family_count < 3
        and not signals.platform_matches
    ):
        return blocked_result("external_context", signals.external_matches)

    has_agent_registry_cue = any(
        token.startswith(prefix)
        for token in signals.tokens
        for prefix in ("ativ", "cadastr", "exist")
    )
    if (
        signals.entity_matches
        and has_agent_registry_cue
        and (signals.query_matches or signals.intent_matches or signals.pattern_matches)
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="agent_registry_listing",
            matched_terms=signals.entity_matches,
        )

    if signals.entity_matches and signals.metric_matches and (
        signals.query_matches
        or signals.has_analytical_or_time_context
        or signals.platform_matches
        or signals.intent_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="operational_entity_metric",
            matched_terms=signals.entity_matches + signals.metric_matches,
        )

    if signals.strict_metric_matches and signals.has_analytical_or_time_context and (
        signals.query_matches
        or signals.platform_matches
        or signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="operational_metric_with_analytics",
            matched_terms=signals.strict_metric_matches + signals.time_matches,
        )

    if signals.strict_metric_matches and signals.analytical_matches and signals.query_matches:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="operational_metric_ranking_shorthand",
            matched_terms=signals.strict_metric_matches + signals.analytical_matches,
        )

    if signals.entity_matches and (
        signals.metric_matches
        or "ranking" in signals.strong_domain_matches
        or signals.analytical_matches
    ) and (
        signals.query_matches
        or signals.time_matches
        or signals.pattern_matches
        or signals.platform_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="operational_entity_with_analytics",
            matched_terms=(
                signals.entity_matches
                + signals.metric_matches
                + signals.analytical_matches
            ),
        )

    if signals.strong_domain_matches and (
        signals.intent_matches
        or signals.query_matches
        or signals.platform_matches
        or signals.time_matches
        or signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="strong_domain_with_context",
            matched_terms=signals.strong_domain_matches,
        )

    if len(signals.strong_domain_matches) >= 1 and signals.domain_match_count >= 2:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="multiple_domain_terms",
            matched_terms=signals.strong_domain_matches + signals.weak_domain_matches,
        )

    if len(signals.weak_domain_matches) >= 2 and (
        signals.intent_matches
        or signals.query_matches
        or signals.time_matches
        or signals.pattern_matches
        or signals.platform_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="weak_domain_with_context",
            matched_terms=signals.weak_domain_matches,
        )

    if signals.weak_domain_matches and signals.platform_matches and (
        signals.intent_matches or signals.query_matches or signals.time_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="domain_with_platform_context",
            matched_terms=signals.weak_domain_matches + signals.platform_matches,
        )

    if signals.weak_domain_matches and signals.time_matches and signals.query_matches:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="domain_with_time_question",
            matched_terms=signals.weak_domain_matches + signals.time_matches,
        )

    if signals.platform_matches and (
        signals.intent_matches
        or signals.query_matches
        or signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="platform_context_question",
            matched_terms=signals.platform_matches,
        )

    if signals.pattern_matches:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="pattern_match_only",
            matched_terms=signals.pattern_matches,
        )

    if signals.strong_domain_matches and (
        signals.intent_matches
        or signals.query_matches
        or signals.time_matches
        or signals.analytical_matches
        or signals.entity_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="strong_domain_with_any_signal",
            matched_terms=signals.strong_domain_matches,
        )

    if len(signals.strong_domain_matches) >= 2:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="multiple_strong_domain",
            matched_terms=signals.strong_domain_matches,
        )

    if signals.weak_domain_matches and signals.intent_matches:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="weak_domain_with_intent",
            matched_terms=signals.weak_domain_matches + signals.intent_matches,
        )

    return blocked_result("no_scope_match")


def validate_scope(text: str) -> ScopeValidationResult:
    return classify_scope(text)


def validate_assistant_response(
    *,
    user_text: str,
    response_text: str,
    had_tool_calls: bool = False,
) -> ScopeValidationResult:
    if response_text == ASSISTANT_SAFE_FALLBACK_RESPONSE:
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="safe_fallback_response",
        )

    response_signals = analyze_text(response_text)
    if not response_signals.normalized_text:
        return blocked_result("empty_response")

    if response_signals.bypass_matches:
        return blocked_result("response_prompt_injection", response_signals.bypass_matches)

    if response_signals.out_of_scope_matches:
        return blocked_result("response_out_of_scope_phrase", response_signals.out_of_scope_matches)

    if len(response_signals.external_matches) >= 2:
        return blocked_result("response_external_context", response_signals.external_matches)

    user_signals = analyze_text(user_text)
    shared_domain = tuple(
        sorted(
            set(
                user_signals.strong_domain_matches
                + user_signals.weak_domain_matches
                + user_signals.entity_matches
                + user_signals.metric_matches
            )
            & set(
                response_signals.strong_domain_matches
                + response_signals.weak_domain_matches
                + response_signals.entity_matches
                + response_signals.metric_matches
            )
        )
    )

    if had_tool_calls and (
        response_signals.output_confirmation_matches
        or response_signals.output_status_matches
        or response_signals.output_context_request_matches
        or response_signals.domain_match_count
        or response_signals.platform_matches
        or response_signals.entity_matches
        or response_signals.metric_matches
        or response_signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="tool_response_confirmed",
            matched_terms=(
                response_signals.output_confirmation_matches
                + response_signals.output_status_matches
                + response_signals.output_context_request_matches
            ),
        )

    if response_signals.output_context_request_matches and (
        user_signals.has_operational_scope
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_requests_operational_context",
            matched_terms=response_signals.output_context_request_matches,
        )

    if shared_domain and (
        response_signals.domain_match_count
        or response_signals.entity_matches
        or response_signals.metric_matches
        or response_signals.platform_matches
        or response_signals.output_confirmation_matches
        or response_signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_shares_domain_context",
            matched_terms=shared_domain,
        )

    if response_signals.strong_domain_matches and (
        response_signals.platform_matches
        or response_signals.output_confirmation_matches
        or response_signals.intent_matches
        or response_signals.query_matches
        or response_signals.time_matches
        or response_signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_strong_domain_with_context",
            matched_terms=response_signals.strong_domain_matches,
        )

    if response_signals.entity_matches and response_signals.metric_matches and (
        response_signals.has_analytical_or_time_context
        or response_signals.output_confirmation_matches
        or response_signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_operational_entity_metric",
            matched_terms=response_signals.entity_matches + response_signals.metric_matches,
        )

    if response_signals.strict_metric_matches and (
        response_signals.has_analytical_or_time_context
    ) and (
        response_signals.entity_matches
        or response_signals.platform_matches
        or response_signals.pattern_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_operational_metric_with_analytics",
            matched_terms=response_signals.strict_metric_matches + response_signals.time_matches,
        )

    if response_signals.domain_match_count >= 2 and (
        response_signals.platform_matches
        or response_signals.output_confirmation_matches
        or response_signals.time_matches
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_multiple_domain_terms",
            matched_terms=(
                response_signals.strong_domain_matches + response_signals.weak_domain_matches
            ),
        )

    if response_signals.platform_matches and (
        response_signals.output_confirmation_matches
        or response_signals.output_context_request_matches
        or response_signals.domain_match_count
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_platform_context",
            matched_terms=response_signals.platform_matches,
        )

    response_system_usage_matches = _find_prefix_matches(
        response_signals.tokens,
        ASSISTANT_OUTPUT_SYSTEM_USAGE_PREFIXES,
    )
    if response_system_usage_matches and (
        not user_signals.out_of_scope_matches
        and not user_signals.external_matches
        and (
            user_signals.has_operational_scope
            or user_signals.platform_matches
            or user_signals.domain_match_count
            or user_signals.intent_matches
            or user_signals.query_matches
        )
    ):
        return ScopeValidationResult(
            classification=DENTRO_DO_ESCOPO,
            reason="response_system_usage_guidance",
            matched_terms=response_system_usage_matches,
        )

    return blocked_result("response_no_scope_match")
