from django.test import SimpleTestCase

from apps.monitoring.utils import format_seconds_hhmmss


class DurationFormattingTests(SimpleTestCase):
    def test_zero_seconds_formats_as_hhmmss(self):
        self.assertEqual(format_seconds_hhmmss(0), "00:00:00")

    def test_forty_five_minutes_formats_as_hhmmss(self):
        self.assertEqual(format_seconds_hhmmss(45 * 60), "00:45:00")

    def test_three_hours_twenty_one_minutes_formats_as_hhmmss(self):
        self.assertEqual(format_seconds_hhmmss((3 * 3600) + (21 * 60)), "03:21:00")

    def test_one_hour_two_minutes_nine_seconds_formats_as_hhmmss(self):
        self.assertEqual(format_seconds_hhmmss((1 * 3600) + (2 * 60) + 9), "01:02:09")
