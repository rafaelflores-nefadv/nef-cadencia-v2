from django.test import TestCase

from apps.rules.models import SystemConfig, SystemConfigValueType
from apps.rules.services.system_config import get_bool, get_config, get_float, get_int, get_json


class SystemConfigServiceTests(TestCase):
    def test_returns_defaults_when_key_does_not_exist(self):
        self.assertEqual(get_config("MISSING_KEY", default="fallback"), "fallback")
        self.assertEqual(get_int("MISSING_INT", default=7), 7)
        self.assertEqual(get_float("MISSING_FLOAT", default=0.5), 0.5)
        self.assertEqual(get_bool("MISSING_BOOL", default=True), True)
        self.assertEqual(get_json("MISSING_JSON", default={"ok": True}), {"ok": True})

    def test_get_bool_and_get_int_respect_value_type(self):
        SystemConfig.objects.create(
            config_key="FEATURE_ENABLED",
            config_value="true",
            value_type=SystemConfigValueType.BOOL,
        )
        SystemConfig.objects.create(
            config_key="RETRY_COUNT",
            config_value="5",
            value_type=SystemConfigValueType.INT,
        )
        SystemConfig.objects.create(
            config_key="BOOL_AS_INT",
            config_value="false",
            value_type=SystemConfigValueType.BOOL,
        )

        self.assertEqual(get_bool("FEATURE_ENABLED", default=False), True)
        self.assertEqual(get_int("RETRY_COUNT", default=1), 5)
        self.assertEqual(get_int("BOOL_AS_INT", default=9), 0)

    def test_invalid_values_fall_back_to_default(self):
        SystemConfig.objects.create(
            config_key="BROKEN_BOOL",
            config_value="not-a-bool",
            value_type=SystemConfigValueType.BOOL,
        )
        SystemConfig.objects.create(
            config_key="BROKEN_INT",
            config_value="12x",
            value_type=SystemConfigValueType.INT,
        )
        SystemConfig.objects.create(
            config_key="BROKEN_FLOAT",
            config_value="nope",
            value_type=SystemConfigValueType.STRING,
        )
        SystemConfig.objects.create(
            config_key="BROKEN_JSON",
            config_value="{invalid-json}",
            value_type=SystemConfigValueType.JSON,
        )

        self.assertEqual(get_bool("BROKEN_BOOL", default=True), True)
        self.assertEqual(get_int("BROKEN_INT", default=44), 44)
        self.assertEqual(get_float("BROKEN_FLOAT", default=1.25), 1.25)
        self.assertEqual(get_json("BROKEN_JSON", default=["fallback"]), ["fallback"])

    def test_get_json_returns_dict_or_list_for_json_type(self):
        SystemConfig.objects.create(
            config_key="JSON_OBJECT",
            config_value='{"a": 1, "b": "x"}',
            value_type=SystemConfigValueType.JSON,
        )
        SystemConfig.objects.create(
            config_key="JSON_LIST",
            config_value='[1, 2, 3]',
            value_type=SystemConfigValueType.JSON,
        )
        SystemConfig.objects.create(
            config_key="STRING_NOT_JSON_TYPE",
            config_value='{"a": 1}',
            value_type=SystemConfigValueType.STRING,
        )

        self.assertEqual(get_json("JSON_OBJECT", default={}), {"a": 1, "b": "x"})
        self.assertEqual(get_json("JSON_LIST", default=[]), [1, 2, 3])
        self.assertEqual(
            get_json("STRING_NOT_JSON_TYPE", default={"fallback": True}),
            {"fallback": True},
        )
