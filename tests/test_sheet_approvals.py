import datetime as dt
import unittest

import sheet_approvals
from email_dispatcher import _valid_approval
from live_sheets_sync import APPROVAL_BASE_HEADERS

HEADERS = list(APPROVAL_BASE_HEADERS) + sheet_approvals.OUTREACH_HEADERS
DIGEST = "a" * 64
FUTURE = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)).isoformat()
PAST = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()


class FakeWorksheet:
    def __init__(self, data_rows=()):
        self.rows = [
            ["APPROVAL QUEUE — LIVE"],
            ["description"],
            [],
            list(HEADERS),
        ]
        self.rows.extend(list(r) for r in data_rows)
        self.row_count = max(len(self.rows), 500)

    def get_all_values(self):
        return [list(r) for r in self.rows]

    def add_rows(self, count):
        self.row_count += count

    def update(self, values=None, range_name=None):
        first = int("".join(ch for ch in range_name.split(":")[0] if ch.isdigit()))
        while len(self.rows) < first + len(values) - 1:
            self.rows.append([])
        for offset, row in enumerate(values):
            self.rows[first - 1 + offset] = list(row)


def row(**overrides):
    record = {h: "" for h in HEADERS}
    record.update({
        "Approval ID": "A1", "Gate": "G2 Outreach", "Status": "Approved",
        "Recipient": "owner@biz.com", "Domain": "biz.com",
        "Message SHA256": DIGEST, "Expires At": FUTURE,
    })
    record.update(overrides)
    return [record[h] for h in HEADERS]


ITEM = {
    "domain": "biz.com", "recipient": "owner@biz.com", "business": "Biz Co",
    "subject": "Your site has 3 issues", "message_sha256": DIGEST,
}


class LoadSheetApprovalsTests(unittest.TestCase):
    def test_approved_row_becomes_an_approval_record(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([row()]))
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["gate_type"], "G2")
        self.assertEqual(approvals[0]["recipient"], "owner@biz.com")
        self.assertEqual(approvals[0]["message_sha256"], DIGEST)

    def test_pending_and_rejected_rows_authorize_nothing(self):
        for status in ["Pending", "Rejected", "Expired", "Cancelled", ""]:
            self.assertEqual(
                sheet_approvals.load_sheet_approvals(FakeWorksheet([row(Status=status)])), []
            )

    def test_row_missing_message_hash_is_ignored(self):
        """A row with no hash would otherwise authorize any message to that domain."""
        for blank in ["Message SHA256", "Recipient", "Domain", "Expires At"]:
            self.assertEqual(
                sheet_approvals.load_sheet_approvals(FakeWorksheet([row(**{blank: ""})])), [],
                f"blank {blank} must not authorize",
            )

    def test_approved_with_conditions_is_honoured(self):
        approvals = sheet_approvals.load_sheet_approvals(
            FakeWorksheet([row(Status="approved with conditions")])
        )
        self.assertEqual(approvals[0]["status"], "Approved with Conditions")

    def test_non_outreach_gates_are_ignored(self):
        self.assertEqual(
            sheet_approvals.load_sheet_approvals(FakeWorksheet([row(Gate="G0 Setup")])), []
        )


class EndToEndGateTests(unittest.TestCase):
    """The dispatcher requires BOTH G2 and G3 for the exact message."""

    def test_one_gate_alone_does_not_authorize(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([row(Gate="G2 Outreach")]))
        ok, missing = _valid_approval(approvals, "owner@biz.com", "biz.com", DIGEST)
        self.assertFalse(ok)
        self.assertEqual(missing, ["G3"])

    def test_both_gates_authorize_the_exact_message(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([
            row(Gate="G2 Outreach"), row(Approval_ID="A2", Gate="G3 Payment"),
        ]))
        ok, missing = _valid_approval(approvals, "owner@biz.com", "biz.com", DIGEST)
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_editing_the_message_voids_the_approval(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([
            row(Gate="G2 Outreach"), row(Gate="G3 Payment"),
        ]))
        ok, _ = _valid_approval(approvals, "owner@biz.com", "biz.com", "b" * 64)
        self.assertFalse(ok, "a different message must not inherit the approval")

    def test_approval_for_one_business_does_not_cover_another(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([
            row(Gate="G2 Outreach"), row(Gate="G3 Payment"),
        ]))
        ok, _ = _valid_approval(approvals, "someone@other.com", "other.com", DIGEST)
        self.assertFalse(ok)

    def test_expired_rows_stop_authorizing(self):
        approvals = sheet_approvals.load_sheet_approvals(FakeWorksheet([
            row(Gate="G2 Outreach", **{"Expires At": PAST}),
            row(Gate="G3 Payment", **{"Expires At": PAST}),
        ]))
        ok, _ = _valid_approval(approvals, "owner@biz.com", "biz.com", DIGEST)
        self.assertFalse(ok)


class StageOutreachApprovalsTests(unittest.TestCase):
    def test_stages_one_row_per_required_gate(self):
        ws = FakeWorksheet()
        staged = sheet_approvals.stage_outreach_approvals(ws, [ITEM])
        self.assertEqual(staged, 2)
        gates = [dict(zip(HEADERS, r))["Gate"] for r in ws.rows[4:]]
        self.assertEqual(sorted(gates), ["G2 Outreach", "G3 Payment"])

    def test_staged_rows_start_pending(self):
        ws = FakeWorksheet()
        sheet_approvals.stage_outreach_approvals(ws, [ITEM])
        for r in ws.rows[4:]:
            record = dict(zip(HEADERS, r))
            self.assertEqual(record["Status"], "Pending")
            self.assertEqual(record["Message SHA256"], DIGEST)
            self.assertTrue(record["Expires At"])

    def test_restaging_does_not_reset_a_decision(self):
        ws = FakeWorksheet()
        sheet_approvals.stage_outreach_approvals(ws, [ITEM])
        decided = dict(zip(HEADERS, ws.rows[4]))
        ws.rows[4][HEADERS.index("Status")] = "Rejected"

        staged = sheet_approvals.stage_outreach_approvals(ws, [ITEM])
        self.assertEqual(staged, 0)
        self.assertEqual(dict(zip(HEADERS, ws.rows[4]))["Status"], "Rejected")
        self.assertEqual(dict(zip(HEADERS, ws.rows[4]))["Gate"], decided["Gate"])

    def test_incomplete_items_are_skipped(self):
        ws = FakeWorksheet()
        staged = sheet_approvals.stage_outreach_approvals(ws, [
            dict(ITEM, recipient=""), dict(ITEM, message_sha256=""), dict(ITEM, domain=""),
        ])
        self.assertEqual(staged, 0)

    def test_staged_row_is_not_itself_an_approval(self):
        ws = FakeWorksheet()
        sheet_approvals.stage_outreach_approvals(ws, [ITEM])
        approvals = sheet_approvals.load_sheet_approvals(ws)
        self.assertEqual(approvals, [], "staging must never self-authorize")


if __name__ == "__main__":
    unittest.main()
