from datetime import time

from django.test import SimpleTestCase

from apps.monitoring.utils import hms_to_seconds


class HmsToSecondsTests(SimpleTestCase):
    def test_converts_hms_string(self):
        self.assertEqual(hms_to_seconds("01:02:03"), 3723)

    def test_converts_time_object(self):
        self.assertEqual(hms_to_seconds(time(2, 10, 5)), 7805)

    def test_returns_none_for_invalid_strings(self):
        self.assertIsNone(hms_to_seconds(""))
        self.assertIsNone(hms_to_seconds("10:20"))
        self.assertIsNone(hms_to_seconds("10:99:00"))
        self.assertIsNone(hms_to_seconds("abc"))
