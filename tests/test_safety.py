import datetime as dt
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import email_dispatcher


class DispatcherSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp.name)
        Path("proposals_asheville").mkdir()
        self.recipient = "owner@example.com"
        self.domain = "example.com"
        self.body = "Subject: Exact approved message\n\nProposal https://example.invalid/pay"
        Path("proposals_asheville/example_com_proposal.txt").write_text(self.body, encoding="utf-8")
        Path("audit_results_asheville.json").write_text(json.dumps([{
            "status": "AUDITED", "domain": self.domain,
            "contacts": {"emails": [self.recipient]},
        }]), encoding="utf-8")

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def _digest(self):
        payload = f"{self.recipient}\nExact approved message\n{self.body}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _write_approvals(self):
        expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
        records = [{
            "gate_type": gate, "status": "Approved", "expires_at": expiry,
            "recipient": self.recipient, "domain": self.domain,
            "message_sha256": self._digest(),
        } for gate in ("G2", "G3")]
        Path("approvals.local.json").write_text(json.dumps(records), encoding="utf-8")

    def test_missing_approvals_fail_closed(self):
        self.assertFalse(email_dispatcher.dispatch_emails())
        self.assertFalse(Path("sent_ledger.local.jsonl").exists())

    def test_exact_approvals_allow_dry_run_without_side_effect(self):
        self._write_approvals()
        self.assertTrue(email_dispatcher.dispatch_emails())
        self.assertFalse(Path("sent_ledger.local.jsonl").exists())

    def test_dnc_overrides_approvals(self):
        self._write_approvals()
        Path("dnc.local.json").write_text(json.dumps([self.recipient]), encoding="utf-8")
        self.assertFalse(email_dispatcher.dispatch_emails())

    def test_sent_ledger_prevents_duplicate(self):
        self._write_approvals()
        Path("sent_ledger.local.jsonl").write_text(
            json.dumps({"message_sha256": self._digest()}) + "\n", encoding="utf-8"
        )
        self.assertTrue(email_dispatcher.dispatch_emails())

    def test_staging_distinguishes_not_yet_approved_from_broken(self):
        """
        The daily pipeline stages decisions, so "nothing is approved yet" is the
        normal state and must not read as a failure — otherwise the run reports
        a failure every single day and the summary stops meaning anything.
        The boolean contract used by --execute stays strict.
        """
        outcome = email_dispatcher.run_dispatch()
        self.assertIsNone(outcome["error"], "an unapproved prospect is not an error")
        self.assertGreater(outcome["blocked"], 0)
        self.assertFalse(email_dispatcher.dispatch_emails(),
                         "the strict view still reports blocked work")

    def test_a_real_fault_is_still_an_error(self):
        Path("audit_results_asheville.json").unlink()
        outcome = email_dispatcher.run_dispatch()
        self.assertIsNotNone(outcome["error"])


if __name__ == "__main__":
    unittest.main()
