import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import live_sheets_sync
from process_intake_queue import build_change_packet


class FakeWorksheet:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.updated_ranges = []

    def get_all_values(self):
        return [list(row) for row in self.rows]

    def append_row(self, row):
        self.rows.append(list(row))

    def update(self, cell_range, values):
        self.updated_ranges.append((cell_range, values))
        row_number = int("".join(ch for ch in cell_range.split(":")[0] if ch.isdigit()))
        self.rows[row_number - 1] = list(values[0])


class FakeSheet:
    def __init__(self):
        self.tabs = {
            "Approval Queue": FakeWorksheet([
                ["APPROVAL QUEUE - LIVE"],
                ["Instructions"],
                [""],
                ["Approval ID", "Requested At", "Run ID", "Requesting Agent", "Gate", "Idea ID", "Business", "Proposed Action", "Evidence / Reason", "Risk / Cost", "Status", "Decision By", "Decision At", "Conditions / Notes", "Expires At"],
                ["", "", "", "", "G0 Setup", "IDEA-01", "", "", "", "", "Pending", "", "", "", ""],
            ]),
            "Activity Log": FakeWorksheet(),
        }

    def worksheet(self, name):
        return self.tabs[name]


class IntakeSheetSyncTests(unittest.TestCase):
    def test_atlas_writer_appends_once_and_audits(self):
        record = {
            "requestId": "req-123", "source": "universal-ai-workforce-website",
            "submittedAt": "2026-08-06T12:00:00+00:00",
            "payload": {"name": "Jane", "email": "jane@example.com", "startingPoint": "existing_business"},
        }
        packet = build_change_packet(record)
        sheet = FakeSheet()
        with tempfile.TemporaryDirectory() as folder:
            packet_file = Path(folder) / "packets.json"
            packet_file.write_text(json.dumps([packet]), encoding="utf-8")
            with patch.dict(os.environ, {"WORKFORCE_INTAKE_BACKEND": "firestore"}), patch.object(live_sheets_sync, "INTAKE_PACKET_FILE", str(packet_file)), patch("intake_store.firestore_store_from_env"):
                self.assertEqual(live_sheets_sync.sync_intake_packets(sheet), 1)
                self.assertEqual(live_sheets_sync.sync_intake_packets(sheet), 0)
        approval_rows = sheet.tabs["Approval Queue"].rows
        self.assertEqual(len(approval_rows), 6)
        self.assertIn("Request ID", approval_rows[3])
        self.assertEqual(approval_rows[-1][0], "req-123")
        self.assertEqual(len(sheet.tabs["Activity Log"].rows), 1)

    def test_unknown_existing_headers_fail_closed(self):
        sheet = FakeSheet()
        sheet.tabs["Approval Queue"].rows = [["Unknown Column"]]
        with tempfile.TemporaryDirectory() as folder:
            packet_file = Path(folder) / "packets.json"
            packet_file.write_text(json.dumps([{"agent": "Atlas-Orchestrator", "external_action_taken": False,
                "proposed_sheet_changes": [{"tab": "Approval Queue"}]}]), encoding="utf-8")
            with patch.dict(os.environ, {"WORKFORCE_INTAKE_BACKEND": "firestore"}), patch.object(live_sheets_sync, "INTAKE_PACKET_FILE", str(packet_file)):
                with self.assertRaises(ValueError):
                    live_sheets_sync.sync_intake_packets(sheet)


if __name__ == "__main__":
    unittest.main()
