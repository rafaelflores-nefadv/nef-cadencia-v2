from django.test import TestCase

from apps.assistant.services.openai_settings import get_openai_settings
from apps.rules.models import SystemConfig, SystemConfigValueType


class OpenAISettingsTests(TestCase):
    def test_returns_defaults_when_system_config_is_missing(self):
        settings = get_openai_settings()

        self.assertEqual(
            settings,
            {
                "enabled": True,
                "model": "gpt-4.1-mini",
                "temperature": 0.2,
                "max_output_tokens": 600,
                "timeout_seconds": 30,
            },
        )

    def test_returns_values_from_system_config_when_present(self):
        SystemConfig.objects.create(
            config_key="OPENAI_ENABLED",
            config_value="false",
            value_type=SystemConfigValueType.BOOL,
        )
        SystemConfig.objects.create(
            config_key="OPENAI_MODEL",
            config_value="gpt-4.1",
            value_type=SystemConfigValueType.STRING,
        )
        SystemConfig.objects.create(
            config_key="OPENAI_TEMPERATURE",
            config_value="0.55",
            value_type=SystemConfigValueType.STRING,
        )
        SystemConfig.objects.create(
            config_key="OPENAI_MAX_OUTPUT_TOKENS",
            config_value="900",
            value_type=SystemConfigValueType.INT,
        )
        SystemConfig.objects.create(
            config_key="OPENAI_TIMEOUT_SECONDS",
            config_value="45",
            value_type=SystemConfigValueType.INT,
        )

        settings = get_openai_settings()

        self.assertEqual(settings["enabled"], False)
        self.assertEqual(settings["model"], "gpt-4.1")
        self.assertEqual(settings["temperature"], 0.55)
        self.assertEqual(settings["max_output_tokens"], 900)
        self.assertEqual(settings["timeout_seconds"], 45)
