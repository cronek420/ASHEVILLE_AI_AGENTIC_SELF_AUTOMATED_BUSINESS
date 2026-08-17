import unittest

from process_intake_queue import build_change_packet


class IntakeQueueTests(unittest.TestCase):
    def test_packet_targets_approval_queue_without_external_action(self):
        packet = build_change_packet({
            "requestId": "abc123", "status": "NEEDS_OWNER_REVIEW", "mode": "DRY_RUN",
            "source": "universal-ai-workforce-website", "submittedAt": "2026-08-06T12:00:00+00:00",
            "payload": {"name": "Jane", "email": "jane@example.com", "startingPoint": "existing_business"},
        })
        self.assertEqual(packet["agent"], "Atlas-Orchestrator")
        self.assertFalse(packet["external_action_taken"])
        self.assertEqual(packet["proposed_sheet_changes"][0]["tab"], "Approval Queue")
        fields = packet["proposed_sheet_changes"][0]["fields"]
        self.assertEqual(fields["Status"], "NEEDS_OWNER_REVIEW")
        self.assertEqual(fields["Mode"], "DRY_RUN")


if __name__ == "__main__":
    unittest.main()
