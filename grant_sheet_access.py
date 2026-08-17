"""
Share the Command Center workbooks with the Cloud Run job's service account.

Sheets and Drive permissions come from document sharing, not project IAM, so
granting Editor here adds no project privileges to the account — it can reach
exactly the files listed below and nothing else.

Run this once, locally, as the account that owns the workbooks:

    python grant_sheet_access.py                 # show what would change
    python grant_sheet_access.py --execute       # apply it

To undo, remove the service account from the file's Share dialog, or:

    python grant_sheet_access.py --revoke --execute
"""

import argparse
import sys

import yaml
from googleapiclient.discovery import build

import agency_auth

# The identity attached to Cloud Run job `agency-pipeline`.
# Changed 2026-08-09 when the job moved off the broad default compute account.
# If this drifts from the job's real identity, a newly added city is shared with
# the wrong account and its sync fails with a confusing permission error, so
# check it against:
#   gcloud run jobs describe agency-pipeline --region=us-east1 \
#     --format="value(spec.template.spec.template.spec.serviceAccountName)"
DEFAULT_SERVICE_ACCOUNT = "agency-pipeline-runtime@asheville-ai-agentic-automate.iam.gserviceaccount.com"
DRIVE_FOLDER_ID = "14bNYctr5hoYcOhSCdWXOvPMS6qVMru10"
ROLE = "writer"


def targets():
    """Every file the pipeline must be able to write, with a human label."""
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        tenants = (yaml.safe_load(handle) or {}).get("tenants", {}) or {}

    found = [("Drive folder", DRIVE_FOLDER_ID)]
    for name, config in tenants.items():
        spreadsheet_id = config.get("spreadsheet_id")
        if spreadsheet_id:
            found.append((f"{name} Command Center", spreadsheet_id))
    return found


def existing_grant(drive, file_id, email):
    """Return the permission id for `email` on this file, or None."""
    response = drive.permissions().list(
        fileId=file_id,
        fields="permissions(id,emailAddress,role)",
        supportsAllDrives=True,
    ).execute()
    for permission in response.get("permissions", []):
        if (permission.get("emailAddress") or "").lower() == email.lower():
            return permission
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service-account", default=DEFAULT_SERVICE_ACCOUNT)
    parser.add_argument("--execute", action="store_true",
                        help="Apply the changes. Without this, nothing is modified.")
    parser.add_argument("--revoke", action="store_true",
                        help="Remove the grant instead of adding it.")
    args = parser.parse_args()

    email = args.service_account
    creds = agency_auth.oauth_credentials()
    drive = build("drive", "v3", credentials=creds)

    verb = "Revoking" if args.revoke else "Granting"
    mode = "EXECUTE" if args.execute else "DRY RUN — nothing will be modified"
    print(f"{verb} '{ROLE}' for {email}")
    print(f"Mode: {mode}\n")

    changed = 0
    for label, file_id in targets():
        try:
            current = existing_grant(drive, file_id, email)
        except Exception as exc:
            print(f"  [SKIP] {label} ({file_id}): cannot read permissions: {exc}")
            continue

        if args.revoke:
            if not current:
                print(f"  [OK]   {label}: no grant to remove.")
                continue
            if not args.execute:
                print(f"  [WOULD REVOKE] {label} ({file_id})")
                changed += 1
                continue
            drive.permissions().delete(fileId=file_id, permissionId=current["id"],
                                       supportsAllDrives=True).execute()
            print(f"  [REVOKED] {label}")
            changed += 1
            continue

        if current and current.get("role") in {"writer", "owner", "organizer"}:
            print(f"  [OK]   {label}: already has '{current['role']}'.")
            continue
        if not args.execute:
            print(f"  [WOULD GRANT] {label} ({file_id})")
            changed += 1
            continue

        drive.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": ROLE, "emailAddress": email},
            # A service account has no mailbox; a notification would only bounce.
            sendNotificationEmail=False,
            supportsAllDrives=True,
        ).execute()
        print(f"  [GRANTED] {label}")
        changed += 1

    print()
    if not args.execute and changed:
        print(f"{changed} change(s) pending. Re-run with --execute to apply.")
    elif not changed:
        print("Nothing to do; access is already as requested.")
    else:
        print(f"{changed} change(s) applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
