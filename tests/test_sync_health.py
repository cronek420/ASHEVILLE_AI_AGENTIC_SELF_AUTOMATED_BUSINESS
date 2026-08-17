"""
The daily report must make a do-nothing run impossible to miss.

For three days in August 2026 every cloud run reported "11 passed, 0 failed"
while writing nothing to the Command Center. Counting leads and proposals did
not catch it, because those files were produced normally. Only the number of
rows actually written to the sheet would have.
"""

import unittest

import daily_reporter


def health(syncs, inbox_ok=True, unread=0, inbox_recorded=True):
    return {
        "syncs": syncs,
        "inbox_ok": inbox_ok,
        "inbox_recorded": inbox_recorded,
        "unread": unread,
    }


def sync(tenant, ok=True, appended=0, updated=0, recorded=True, error=""):
    return {
        "tenant": tenant, "ok": ok, "appended": appended,
        "updated": updated, "recorded": recorded, "error": error,
    }


class SyncHealthBlockTests(unittest.TestCase):
    def test_a_healthy_run_carries_no_alarm(self):
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", appended=21, updated=24)]))
        self.assertNotIn("ATTENTION", block)
        self.assertIn("wrote 45 row(s)", block)
        self.assertIn("21 new, 24 updated", block)

    def test_a_failed_sync_raises_the_alarm_and_names_the_city(self):
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", appended=21, updated=24),
                    sync("charlotte", ok=False, error="read-only token mount")]))
        self.assertIn("ATTENTION", block)
        self.assertIn("charlotte", block)
        self.assertIn("SYNC FAILED", block)
        self.assertIn("read-only token mount", block)

    def test_a_step_that_never_ran_is_reported_as_missing_not_as_zero(self):
        """Absent evidence and evidence of zero are different problems."""
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", recorded=False, ok=False)]))
        self.assertIn("NO SYNC RECORDED", block)
        self.assertIn("ATTENTION", block)

    def test_connected_but_zero_rows_is_flagged_without_crying_failure(self):
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", appended=0, updated=0)]))
        self.assertIn("no rows changed", block)
        self.assertNotIn("ATTENTION", block)

    def test_an_unreadable_mailbox_raises_the_alarm(self):
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", appended=1)], inbox_ok=False, inbox_recorded=False))
        self.assertIn("NOT CHECKED", block)
        self.assertIn("ATTENTION", block)

    def test_unread_count_is_reported_when_the_mailbox_was_read(self):
        block = daily_reporter.build_sync_health_block(
            health([sync("asheville", appended=1)], unread=7))
        self.assertIn("7 unread", block)

    def test_the_block_leads_the_report_body(self):
        body = daily_reporter.build_report_content(
            config={}, stats={"scraped_leads": 0, "audits": 0, "proposals_generated": 0,
                              "error_count": 0, "recent_errors": []},
            sync_health=health([sync("asheville", ok=False)]))
        self.assertIn("ATTENTION", body)
        self.assertLess(body.index("ATTENTION"), body.index("QUICK STATS"),
                        "a do-nothing run must appear above the routine numbers")


if __name__ == "__main__":
    unittest.main()
