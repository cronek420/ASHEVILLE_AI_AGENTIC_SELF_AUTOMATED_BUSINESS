import os
import tempfile
import unittest

import daily_reporter


class DailyReporterTests(unittest.TestCase):
    def test_report_explains_pending_deployment_and_links(self):
        content = daily_reporter.build_report_content(
            config={
                "command_center_url": "https://sheet.example",
                "drive_url": "https://drive.example",
                "website_origin": "https://site.example",
                "approval_summary": "Approval is still pending.",
            },
            stats={
                "scraped_leads": 5,
                "audits": 4,
                "proposals_generated": 3,
                "error_count": 0,
                "recent_errors": [],
            },
        )
        self.assertIn("Live intake link: pending Gate B deployment approval", content)
        self.assertIn(f"https://sheet.example#gid={daily_reporter.LIVE_DASHBOARD_GID} (Live Dashboard)", content)
        self.assertIn(f"https://sheet.example#gid={daily_reporter.APPROVAL_QUEUE_GID} (Approval Queue)", content)
        self.assertIn(f"https://sheet.example#gid={daily_reporter.PROSPECT_TRACKER_GID} (Prospect Tracker)", content)
        self.assertIn("Approval is still pending.", content)
        self.assertIn("No urgent intervention is required", content)
        self.assertIn("screenshot proof", content)

    def test_report_includes_live_intake_link_and_recent_errors(self):
        content = daily_reporter.build_report_content(
            config={
                "intake_public_url": "https://api.example/v1/public/onboarding-requests",
                "approval_summary": "Deployed and ready.",
            },
            stats={
                "scraped_leads": 1,
                "audits": 2,
                "proposals_generated": 3,
                "error_count": 2,
                "recent_errors": ["[ERROR] sample one", "[ERROR] sample two"],
            },
        )
        self.assertIn("Live intake link: https://api.example/v1/public/onboarding-requests", content)
        self.assertIn("Action needed today:", content)
        self.assertIn("[ERROR] sample one", content)

    def test_each_tenant_links_to_its_own_spreadsheet(self):
        content = daily_reporter.build_report_content(
            config={"command_center_url": "https://shared.example"},
            stats={
                "scraped_leads": 0,
                "audits": 0,
                "proposals_generated": 0,
                "error_count": 0,
                "recent_errors": [],
            },
            tenant_links=[
                {
                    "tenant": "asheville",
                    "url": "https://sheet.example/ash",
                    "live_dashboard": "111",
                    "approval_queue": "222",
                    "prospect_tracker": "333",
                },
                {
                    "tenant": "charlotte",
                    "url": "https://sheet.example/clt",
                    "live_dashboard": "444",
                    "approval_queue": "555",
                    "prospect_tracker": "666",
                },
            ],
        )
        self.assertIn("-- ASHEVILLE --", content)
        self.assertIn("https://sheet.example/ash#gid=222 (Approval Queue)", content)
        self.assertIn("-- CHARLOTTE --", content)
        self.assertIn("https://sheet.example/clt#gid=666 (Prospect Tracker)", content)
        # The shared fallback URL must not leak into a per-tenant report.
        self.assertNotIn("https://shared.example#gid=", content)

    def test_quick_stats_are_reported_per_tenant(self):
        content = daily_reporter.build_report_content(
            config={},
            stats={
                "scraped_leads": 99,
                "audits": 99,
                "proposals_generated": 99,
                "error_count": 0,
                "recent_errors": [],
            },
            tenant_stats=[
                {"tenant": "asheville", "scraped_leads": 19, "audits": 19, "proposals_generated": 11},
                {"tenant": "charlotte", "scraped_leads": 8, "audits": 8, "proposals_generated": 19},
            ],
        )
        self.assertIn("-- ASHEVILLE --", content)
        self.assertIn("• Proposals: 11", content)
        self.assertIn("• Proposals: 19", content)
        self.assertIn("• Errors (last run): 0", content)
        # Legacy single-city totals must not be presented as a city's numbers.
        self.assertNotIn("• Proposals: 99", content)


class ScanRunErrorsTests(unittest.TestCase):
    def _write_log(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_errors_from_previous_runs_are_excluded(self):
        log = self._write_log(
            "  Run started: 2026-08-06T05:00:00\n"
            "[ERROR] old failure that was already fixed\n"
            "[ERROR] another stale one\n"
            "  Run started: 2026-08-09T01:00:00\n"
            "[INFO] all good\n"
            "[ERROR] current failure\n"
        )
        count, recent = daily_reporter._scan_run_errors(log)
        self.assertEqual(count, 1)
        self.assertEqual(recent, ["[ERROR] current failure"])

    def test_clean_latest_run_reports_zero_despite_history(self):
        log = self._write_log(
            "  Run started: 2026-08-06T05:00:00\n"
            "[ERROR] historical failure\n"
            "Traceback (most recent call last):\n"
            "  Run started: 2026-08-09T01:00:00\n"
            "[INFO] pipeline complete\n"
        )
        count, recent = daily_reporter._scan_run_errors(log)
        self.assertEqual(count, 0)
        self.assertEqual(recent, [])

    def test_missing_marker_falls_back_to_whole_file(self):
        log = self._write_log("[ERROR] one\n[ERROR] two\n")
        count, _ = daily_reporter._scan_run_errors(log)
        self.assertEqual(count, 2)

    def test_keeps_the_most_recent_errors_not_the_oldest(self):
        log = self._write_log(
            "  Run started: 2026-08-09T01:00:00\n"
            + "".join(f"[ERROR] failure {n}\n" for n in range(1, 6))
        )
        count, recent = daily_reporter._scan_run_errors(log)
        self.assertEqual(count, 5)
        self.assertEqual(recent, ["[ERROR] failure 3", "[ERROR] failure 4", "[ERROR] failure 5"])

    def test_missing_log_is_not_an_error(self):
        count, recent = daily_reporter._scan_run_errors("does_not_exist.log")
        self.assertEqual((count, recent), (0, []))


