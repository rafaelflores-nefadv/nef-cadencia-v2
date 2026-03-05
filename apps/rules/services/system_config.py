import json
from typing import Any

from apps.rules.models import SystemConfig, SystemConfigValueType

_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}
_FALSE_VALUES = {"0", "false", "no", "off", "n", "f"}


def _get_system_config(key: str) -> SystemConfig | None:
    return (
        SystemConfig.objects
        .filter(config_key=key)
        .only("config_key", "config_value", "value_type")
        .first()
    )


def _parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return None

    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None


def _parse_typed_value(config: SystemConfig) -> Any:
    raw_value = config.config_value
    value_type = config.value_type

    if value_type == SystemConfigValueType.BOOL:
        parsed = _parse_bool(raw_value)
        if parsed is None:
            raise ValueError("Invalid bool value")
        return parsed

    if value_type == SystemConfigValueType.INT:
        return int(str(raw_value).strip())

    if value_type == SystemConfigValueType.JSON:
        return json.loads(raw_value)

    # STRING/TIME e demais tipos permanecem em formato texto.
    return str(raw_value).strip()


def get_config(key: str, default=None) -> str | None:
    config = _get_system_config(key)
    if config is None:
        return default

    value = (config.config_value or "").strip()
    if value == "":
        return default
    return value


def get_int(key: str, default: int) -> int:
    config = _get_system_config(key)
    if config is None:
        return default

    try:
        parsed = _parse_typed_value(config)
        if isinstance(parsed, bool):
            return int(parsed)
        if isinstance(parsed, int):
            return parsed
        if isinstance(parsed, float):
            return int(parsed)
        if isinstance(parsed, str):
            return int(parsed.strip())
        return default
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def get_bool(key: str, default: bool) -> bool:
    config = _get_system_config(key)
    if config is None:
        return default

    try:
        parsed = _parse_typed_value(config)
        if isinstance(parsed, bool):
            return parsed
        if isinstance(parsed, (int, float)):
            return bool(parsed)

        coerced = _parse_bool(parsed)
        if coerced is None:
            return default
        return coerced
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def get_json(key: str, default):
    config = _get_system_config(key)
    if config is None:
        return default

    try:
        parsed = _parse_typed_value(config)
        if isinstance(parsed, (dict, list)):
            return parsed
        return default
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def get_float(key: str, default: float) -> float:
    config = _get_system_config(key)
    if config is None:
        return default

    try:
        parsed = _parse_typed_value(config)
        if isinstance(parsed, bool):
            return float(int(parsed))
        if isinstance(parsed, (int, float)):
            return float(parsed)
        if isinstance(parsed, str):
            return float(parsed.strip())
        return default
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
