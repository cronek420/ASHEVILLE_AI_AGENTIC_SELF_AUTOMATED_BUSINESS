"""
The ledger answers "who have we already emailed, and who must we never email".

Both questions fail in the same dangerous direction: an empty answer reads as
permission to send. These tests pin the safe direction — when the record cannot
be trusted, nothing may be sent.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import email_dispatcher
import outreach_ledger


class SuppressionParsingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dnc = Path(self.tmp.name) / "dnc.json"

    def _ledger(self):
        return outreach_ledger.OutreachLedger(
            ledger_file=Path(self.tmp.name) / "ledger.jsonl",
            dnc_file=self.dnc,
            require_durable=False,
            use_firestore=False,
        )

    def test_plain_string_entries_are_supported(self):
        self.dnc.write_text(json.dumps(["A@Example.com "]), encoding="utf-8")
        self.assertEqual(self._ledger().suppressed(), {"a@example.com"})

    def test_object_entries_carry_their_reason_and_still_block(self):
        self.dnc.write_text(json.dumps([
            {"address": "info@dead.com", "reason": "hard bounce"},
        ]), encoding="utf-8")
        self.assertEqual(self._ledger().suppressed(), {"info@dead.com"})

    def test_mixed_formats_coexist(self):
        self.dnc.write_text(json.dumps([
            "old@example.com",
            {"address": "new@example.com", "reason": "bounce"},
        ]), encoding="utf-8")
        self.assertEqual(self._ledger().suppressed(),
                         {"old@example.com", "new@example.com"})

    def test_a_corrupt_suppression_file_blocks_rather_than_unblocks(self):
        """Malformed JSON must never be read as 'nobody is suppressed'."""
        self.dnc.write_text("{not json", encoding="utf-8")
        with self.assertRaises(outreach_ledger.LedgerUnavailable):
            self._ledger().suppressed()

    def test_absent_file_is_simply_empty(self):
        self.assertEqual(self._ledger().suppressed(), set())


class DurabilityRequiredTests(unittest.TestCase):
    """In Cloud Run the local files cannot persist, so Firestore is mandatory."""

    def _cloud_ledger(self, client=None):
        ledger = outreach_ledger.OutreachLedger(
            firestore_client=client, require_durable=True, use_firestore=True)
        if client is None:
            # Simulate a backend that cannot be constructed.
            ledger._client_attempted = True
            ledger._client = None
            ledger._client_error = RuntimeError("no credentials")
        return ledger

    def test_reads_refuse_rather_than_return_empty(self):
        ledger = self._cloud_ledger()
        for reader in (ledger.sent_hashes, ledger.suppressed, ledger.sent_recipients):
            with self.assertRaises(outreach_ledger.LedgerUnavailable):
                reader()

    def test_a_send_that_cannot_be_recorded_raises(self):
        ledger = self._cloud_ledger()
        with self.assertRaises(outreach_ledger.LedgerUnavailable):
            ledger.record_send("a@b.com", "b.com", "hash123")

    def test_defaults_to_required_inside_cloud_run(self):
        with mock.patch.dict("os.environ", {"CLOUD_RUN_JOB": "agency-pipeline"}):
            ledger = outreach_ledger.OutreachLedger()
        self.assertTrue(ledger.require_durable)
        self.assertTrue(ledger.use_firestore)

    def test_stays_local_and_offline_outside_cloud_run(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            ledger = outreach_ledger.OutreachLedger()
        self.assertFalse(ledger.require_durable)
        self.assertFalse(ledger.use_firestore,
                         "a local run must not make surprise network calls")


class DispatcherFailsClosedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "audit_results_t.json").write_text(json.dumps([{
            "domain": "example.com",
            "status": "AUDITED",
            "contacts": {"emails": ["owner@example.com"]},
        }]), encoding="utf-8")
        self.root = root

    def test_no_sends_when_the_ledger_cannot_be_read(self):
        broken = mock.MagicMock()
        broken.suppressed.side_effect = outreach_ledger.LedgerUnavailable("backend down")

        with mock.patch.object(email_dispatcher, "_open_ledger", return_value=broken), \
             mock.patch.object(email_dispatcher.Path, "exists", return_value=True), \
             mock.patch.object(email_dispatcher, "_load_json", return_value=[]):
            result = email_dispatcher.dispatch_emails(
                execute=False, tenant="t", use_sheet_approvals=False)

        self.assertFalse(result, "an unreadable ledger must not authorize sending")


if __name__ == "__main__":
    unittest.main()
