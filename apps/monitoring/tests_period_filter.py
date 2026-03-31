from django.test import SimpleTestCase

from apps.monitoring.services.dashboard_period_filter import resolve_dashboard_period_filter


class DashboardPeriodFilterTests(SimpleTestCase):
    def test_explicit_date_range_overrides_quick_range(self):
        result = resolve_dashboard_period_filter(
            {
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "quick_range": "this_month",
            }
        )

        self.assertEqual(result.mode, "custom_range")
        self.assertEqual(result.date_from.isoformat(), "2026-01-01")
        self.assertEqual(result.date_to.isoformat(), "2026-01-31")

    def test_year_month_overrides_quick_range_when_no_explicit_dates(self):
        result = resolve_dashboard_period_filter(
            {
                "year": "2026",
                "month": "1",
                "quick_range": "this_month",
            }
        )

        self.assertEqual(result.mode, "year_month")
        self.assertEqual(result.date_from.isoformat(), "2026-01-01")
        self.assertEqual(result.date_to.isoformat(), "2026-01-31")
