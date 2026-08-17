import unittest

import live_sheets_sync as sync


class FakeWorksheet:
    """
    Minimal gspread stand-in.

    Models a fixed grid: writes past row_count are refused, the way the real API
    silently fails to advance an append target on a pre-filled sheet.
    """

    def __init__(self, rows=None, row_count=None):
        self.rows = [list(row) for row in (rows or [])]
        self.row_count = row_count if row_count is not None else max(len(self.rows), 1000)

    def get_all_values(self):
        return [list(row) for row in self.rows]

    def add_rows(self, count):
        self.row_count += count

    def update(self, values=None, range_name=None):
        first = int("".join(ch for ch in range_name.split(":")[0] if ch.isdigit()))
        if first + len(values) - 1 > self.row_count:
            raise AssertionError(
                f"write to row {first + len(values) - 1} exceeds grid of {self.row_count}"
            )
        while len(self.rows) < first + len(values) - 1:
            self.rows.append([])
        for offset, row in enumerate(values):
            self.rows[first - 1 + offset] = list(row)


def template_tab(extra_rows=()):
    """The workbook template: title, description, blank, then the real header."""
    rows = [
        ["PROSPECT TRACKER — LIVE"],
        ["LIVE TAB — update after every research, contact, reply, or payment event."],
        [],
        list(sync.PROSPECT_TEMPLATE_HEADERS),
    ]
    rows.extend(list(row) for row in extra_rows)
    return FakeWorksheet(rows)


PROSPECT = {
    "name": "Gibson Pest Control",
    "domain": "gibsonpest.com",
    "niche": "Pest Control",
    "score": 93,
    "grade": "A",
    "status": "Audited / Proposal Drafted",
    "issues": "1",
    "top_opportunity": "Social Sharing Preview Setup",
    "phone": "828-684-1353",
    "email": "",
}


class ProspectTrackerSyncTests(unittest.TestCase):
    def test_writes_under_the_real_header_not_row_one(self):
        ws = template_tab()
        appended, updated = sync.sync_prospect_tracker(ws, [PROSPECT])

        self.assertEqual((appended, updated), (1, 0))
        headers = ws.rows[3]
        row = dict(zip(headers, ws.rows[4]))
        self.assertEqual(row["Business"], "Gibson Pest Control")
        self.assertEqual(row["Website"], "gibsonpest.com")
        self.assertEqual(row["Audit Score"], "93")
        self.assertEqual(row["Grade"], "A")
        # The title row must survive untouched.
        self.assertEqual(ws.rows[0], ["PROSPECT TRACKER — LIVE"])

    def test_audit_columns_are_added_to_the_template_header(self):
        ws = template_tab()
        sync.sync_prospect_tracker(ws, [PROSPECT])
        for header in sync.PROSPECT_AUDIT_HEADERS:
            self.assertIn(header, ws.rows[3])

    def test_owner_columns_survive_a_resync(self):
        ws = template_tab()
        sync.sync_prospect_tracker(ws, [PROSPECT])
        headers = ws.rows[3]

        # Owner fills in the commercial columns by hand.
        row = ws.rows[4]
        for header, value in [
            ("Date Contacted", "2026-08-09"),
            ("Follow-Up Date", "2026-08-12"),
            ("Quoted Price", "$149"),
            ("Deposit Requested", "$75"),
            ("Status", "Contacted"),
            ("Priority", "Urgent"),
        ]:
            row[headers.index(header)] = value

        # A later run sees an improved score for the same site.
        rescanned = dict(PROSPECT, score=97, top_opportunity="Local Business Schema Markup")
        appended, updated = sync.sync_prospect_tracker(ws, [rescanned])

        self.assertEqual((appended, updated), (0, 1))
        after = dict(zip(headers, ws.rows[4]))
        self.assertEqual(after["Date Contacted"], "2026-08-09")
        self.assertEqual(after["Follow-Up Date"], "2026-08-12")
        self.assertEqual(after["Quoted Price"], "$149")
        self.assertEqual(after["Deposit Requested"], "$75")
        self.assertEqual(after["Status"], "Contacted")
        self.assertEqual(after["Priority"], "Urgent")
        # Agent-owned columns still refresh.
        self.assertEqual(after["Audit Score"], "97")
        self.assertEqual(after["Top Opportunity"], "Local Business Schema Markup")

    def test_unchanged_audit_data_is_not_rewritten(self):
        ws = template_tab()
        sync.sync_prospect_tracker(ws, [PROSPECT])
        appended, updated = sync.sync_prospect_tracker(ws, [PROSPECT])
        self.assertEqual((appended, updated), (0, 0))
        self.assertEqual(len(ws.rows), 5)

    def test_website_matching_ignores_scheme_and_www(self):
        ws = template_tab()
        sync.sync_prospect_tracker(ws, [PROSPECT])
        variant = dict(PROSPECT, domain="https://www.gibsonpest.com/")
        appended, _ = sync.sync_prospect_tracker(ws, [variant])
        self.assertEqual(appended, 0, "same site must not be duplicated")
        self.assertEqual(len(ws.rows), 5)

    def test_new_rows_are_seeded_for_the_owner(self):
        ws = template_tab()
        sync.sync_prospect_tracker(ws, [PROSPECT])
        row = dict(zip(ws.rows[3], ws.rows[4]))
        self.assertEqual(row["Status"], "Not Contacted")
        self.assertEqual(row["Priority"], "High")

    def test_every_new_prospect_lands_on_its_own_row(self):
        """Regression: a per-row append loop against a template that pre-fills
        rows to the bottom of the grid kept only the last prospect."""
        prefilled = [
            ["", "", "", "", "", "", "", "", "", "", "Not Contacted", "", "", ""]
            for _ in range(200)
        ]
        ws = template_tab(prefilled)
        ws.row_count = len(ws.rows)

        batch = [
            dict(PROSPECT, name=f"Business {n}", domain=f"site{n}.com")
            for n in range(1, 12)
        ]
        appended, updated = sync.sync_prospect_tracker(ws, batch)

        self.assertEqual((appended, updated), (11, 0))
        headers = ws.rows[3]
        website = headers.index("Website")
        written = {
            row[website] for row in ws.rows[4:]
            if len(row) > website and row[website].strip()
        }
        self.assertEqual(written, {f"site{n}.com" for n in range(1, 12)})

    def test_grid_is_grown_when_new_rows_do_not_fit(self):
        ws = template_tab()
        ws.row_count = 4  # exactly the header, no spare rows
        appended, _ = sync.sync_prospect_tracker(ws, [PROSPECT])
        self.assertEqual(appended, 1)
        self.assertGreaterEqual(ws.row_count, 5)

    def test_duplicate_domains_in_one_batch_collapse(self):
        ws = template_tab()
        appended, _ = sync.sync_prospect_tracker(ws, [PROSPECT, dict(PROSPECT)])
        self.assertEqual(appended, 1)

    def test_legacy_flat_layout_fails_closed(self):
        ws = FakeWorksheet([
            ["Business Name", "Domain", "Niche", "Audit Score", "Grade",
             "Status", "Issues", "Top Opportunity", "Phone", "Email"],
        ])
        with self.assertRaises(ValueError):
            sync.sync_prospect_tracker(ws, [PROSPECT])
        self.assertEqual(len(ws.rows), 1, "must not append misaligned rows")

    def test_empty_tab_gets_the_full_header(self):
        ws = FakeWorksheet()
        appended, _ = sync.sync_prospect_tracker(ws, [PROSPECT])
        self.assertEqual(appended, 1)
        self.assertEqual(ws.rows[0], sync.PROSPECT_HEADERS)


class ApprovalVocabularyTests(unittest.TestCase):
    """The workbook's Gate and Status columns are typed DROPDOWN columns; a value
    outside the list cannot be filtered, coloured, or picked from the dropdown."""

    def test_gate_shorthand_maps_to_workbook_labels(self):
        self.assertEqual(sync.gate_label("G0"), "G0 Setup")
        self.assertEqual(sync.gate_label("G2"), "G2 Outreach")
        self.assertEqual(sync.gate_label("G4"), "G4 Access & Publish")

    def test_already_labelled_gate_is_left_alone(self):
        self.assertEqual(sync.gate_label("G2 Outreach"), "G2 Outreach")

    def test_internal_states_become_pending_not_approved(self):
        for state in ["NEEDS_OWNER_REVIEW", "QUEUED", "", None, "something unexpected"]:
            self.assertEqual(sync.approval_status_label(state), "Pending")

    def test_real_decisions_are_preserved(self):
        self.assertEqual(sync.approval_status_label("Approved"), "Approved")
        self.assertEqual(sync.approval_status_label("approved with conditions"),
                         "Approved with Conditions")
        self.assertEqual(sync.approval_status_label("Rejected"), "Rejected")

    def test_intake_rows_are_written_with_valid_dropdown_values(self):
        fields = sync._row_fields_for_packet(
            {"agent": "Atlas-Orchestrator", "approval_request": "G0", "run_id": "RUN-1"},
            {"Request ID": "req-1", "Status": "NEEDS_OWNER_REVIEW", "Name": "Jane", "Notes": "hello"},
        )
        self.assertEqual(fields["Gate"], "G0 Setup")
        self.assertEqual(fields["Status"], "Pending")
        self.assertIn(fields["Status"], sync.APPROVAL_QUEUE_STATUSES)
        # The raw intake state must not be silently discarded.
        self.assertIn("NEEDS_OWNER_REVIEW", fields["Conditions / Notes"])


class NormalizeSiteTests(unittest.TestCase):
    def test_variants_collapse_to_one_key(self):
        for value in [
            "gibsonpest.com", "www.gibsonpest.com", "http://gibsonpest.com",
            "https://www.gibsonpest.com/", "  GibsonPest.com  ",
        ]:
            self.assertEqual(sync._normalize_site(value), "gibsonpest.com")

    def test_blank_values_are_empty(self):
        self.assertEqual(sync._normalize_site(""), "")
        self.assertEqual(sync._normalize_site(None), "")


if __name__ == "__main__":
    unittest.main()
