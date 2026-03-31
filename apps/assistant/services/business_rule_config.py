from __future__ import annotations

import json
from dataclasses import dataclass

from django.test.testcases import DatabaseOperationForbidden

from apps.rules.models import SystemConfig, SystemConfigValueType


BUSINESS_RULE_CONFIG_KEY_PATTERNS = (
    "assistant.business_rules.{rule_key}",
    "assistant.business_rule.{rule_key}",
    "operational_rules.{rule_key}",
    "operational.rule.{rule_key}",
    "rules.{rule_key}",
    "{rule_key}",
)

_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}


@dataclass(frozen=True)
class BusinessRuleDefinition:
    key: str
    config_key: str
    label: str
    summary: str
    criteria: tuple[str, ...]
    suggested_interpretation: str | None = None


def get_business_rule_definition(rule_key: str) -> BusinessRuleDefinition | None:
    normalized_key = str(rule_key or "").strip()
    if not normalized_key:
        return None

    for config_key in _candidate_config_keys(normalized_key):
        try:
            config = (
                SystemConfig.objects
                .filter(config_key=config_key)
                .only("config_key", "config_value", "value_type")
                .first()
            )
        except DatabaseOperationForbidden:
            return None
        if config is None:
            continue

        parsed_value = _parse_config_value(config)
        definition = _build_definition_from_value(normalized_key, config.config_key, parsed_value)
        if definition is not None:
            return definition

    return None


def _candidate_config_keys(rule_key: str) -> tuple[str, ...]:
    return tuple(pattern.format(rule_key=rule_key) for pattern in BUSINESS_RULE_CONFIG_KEY_PATTERNS)


def _parse_config_value(config: SystemConfig):
    raw_value = config.config_value
    if config.value_type == SystemConfigValueType.JSON:
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return None
    if config.value_type == SystemConfigValueType.INT:
        try:
            return int(str(raw_value).strip())
        except (TypeError, ValueError):
            return None
    if config.value_type == SystemConfigValueType.BOOL:
        normalized = str(raw_value or "").strip().lower()
        if not normalized:
            return None
        return normalized in _TRUE_VALUES

    text_value = str(raw_value or "").strip()
    if text_value.startswith("{") or text_value.startswith("["):
        try:
            return json.loads(text_value)
        except json.JSONDecodeError:
            return text_value
    return text_value or None


def _build_definition_from_value(rule_key: str, config_key: str, value) -> BusinessRuleDefinition | None:
    if value in (None, False, "", [], {}):
        return None

    if isinstance(value, dict):
        label = str(value.get("label") or value.get("name") or rule_key).strip() or rule_key
        summary = str(
            value.get("description")
            or value.get("summary")
            or value.get("definition")
            or value.get("rule")
            or ""
        ).strip()
        suggested_interpretation = str(
            value.get("suggested_interpretation") or value.get("interpretation") or ""
        ).strip() or None
        criteria = _normalize_criteria(
            value.get("criteria")
            or value.get("criterios")
            or value.get("thresholds")
            or value.get("rules")
        )
        if not summary and criteria:
            summary = "Critérios operacionais cadastrados para esta regra."
        if not summary:
            summary = f"Regra operacional configurada em {config_key}."
        return BusinessRuleDefinition(
            key=rule_key,
            config_key=config_key,
            label=label,
            summary=summary,
            criteria=criteria,
            suggested_interpretation=suggested_interpretation,
        )

    if isinstance(value, list):
        criteria = _normalize_criteria(value)
        if not criteria:
            return None
        return BusinessRuleDefinition(
            key=rule_key,
            config_key=config_key,
            label=rule_key,
            summary=f"Regra operacional configurada em {config_key}.",
            criteria=criteria,
        )

    if isinstance(value, bool):
        if not value:
            return None
        return BusinessRuleDefinition(
            key=rule_key,
            config_key=config_key,
            label=rule_key,
            summary=f"Regra operacional ativa em {config_key}.",
            criteria=(),
        )

    text_value = str(value).strip()
    if not text_value:
        return None
    return BusinessRuleDefinition(
        key=rule_key,
        config_key=config_key,
        label=rule_key,
        summary=text_value,
        criteria=(),
    )


def _normalize_criteria(raw_criteria) -> tuple[str, ...]:
    if raw_criteria is None:
        return ()

    if isinstance(raw_criteria, dict):
        normalized = []
        for key, value in raw_criteria.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if key_text and value_text:
                normalized.append(f"{key_text}: {value_text}")
        return tuple(normalized)

    if isinstance(raw_criteria, (list, tuple, set)):
        normalized = []
        for item in raw_criteria:
            item_text = str(item).strip()
            if item_text:
                normalized.append(item_text)
        return tuple(normalized)

    criteria_text = str(raw_criteria).strip()
    return (criteria_text,) if criteria_text else ()
