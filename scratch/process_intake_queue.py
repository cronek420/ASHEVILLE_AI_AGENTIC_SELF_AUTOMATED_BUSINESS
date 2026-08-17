"""Atlas-Orchestrator staging step for private onboarding requests."""

import json
import os
from pathlib import Path

from intake_store import firestore_store_from_env


OUTPUT_PATH = Path(__file__).parent / "intake_change_packets.json"


def build_change_packet(record):
    payload = record["payload"]
    request_id = record["requestId"]
    return {
        "run_id": f"INTAKE-{request_id[:12]}",
        "agent": "Atlas-Orchestrator",
        "idea_id": request_id,
        "task": "Stage public onboarding request for owner review",
        "status": "needs_approval",
        "evidence": [{"source_or_artifact": f"firestore:intake/{request_id}", "observation": "Validated public intake received"}],
        "proposed_sheet_changes": [{"tab": "Approval Queue", "record_key": request_id, "fields": {
            "Request ID": request_id, "Status": "NEEDS_OWNER_REVIEW", "Mode": "DRY_RUN",
            "Source": record["source"], "Submitted At": record["submittedAt"],
            "Name": payload["name"], "Email": payload["email"],
            "Starting Point": payload["startingPoint"], "Company Name": payload.get("companyName", ""),
            "Website": payload.get("website", ""), "Notes": payload.get("notes", ""),
            "External Action Taken": False, "Next Step": "Owner reviews intake request",
        }}],
        "approval_request": "G0", "external_action_taken": False,
        "next_step": "Atlas stages the request in Approval Queue", "uncertainties": [],
    }


def main():
    if os.getenv("WORKFORCE_INTAKE_BACKEND") != "firestore":
        print("[SAFE DEFAULT] Firestore intake processing disabled; no packets staged.")
        return 0
    packets = [build_change_packet(record) for record in firestore_store_from_env().pending_requests()]
    OUTPUT_PATH.write_text(json.dumps(packets, indent=2), encoding="utf-8")
    print(f"[PASS] Staged {len(packets)} intake change packet(s) for Atlas review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
