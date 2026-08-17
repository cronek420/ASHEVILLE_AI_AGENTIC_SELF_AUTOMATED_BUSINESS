"""
Inbox Monitor for Asheville AI Agentic Self-Automated Business.
Checks the lexiconatlas@gmail.com inbox for new prospect replies.
Supports two modes:
  - Single-pass (default when called from pipeline): check once, report, exit
  - Continuous polling (when run directly with --loop flag)
"""

import os
import sys
import time
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'gmail_token.json'
SECRET_TOKEN_FILE = '/secrets/gmail/gmail_token.json'


def _resolve_token_path():
    if os.path.exists(SECRET_TOKEN_FILE):
        return SECRET_TOKEN_FILE
    return TOKEN_FILE


def authenticate_gmail():
    creds = None
    token_path = _resolve_token_path()
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Gmail token expired, refreshing...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Gmail token refresh failed: {e}")
                logger.error("ACTION REQUIRED: Re-run this script locally (with a browser) to re-authorize.")
                return None
            logger.info("Gmail token refreshed successfully.")
            # Best effort only. The refresh above already produced valid
            # credentials; on Cloud Run token_path is a read-only Secret Manager
            # mount, and failing here used to abandon a working session.
            try:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except OSError as persist_err:
                logger.warning(f"Refreshed Gmail token not cached to {token_path}: {persist_err}. "
                               "Continuing with the valid in-memory credentials.")
        else:
            logger.error("No valid Gmail OAuth token and no refresh token available.")
            logger.error("ACTION REQUIRED: Run this script locally (with a browser) to authorize,")
            logger.error("                 then upload gmail_token.json or refresh the Secret Manager mounted token.")
            return None
    return creds


def check_inbox(service):
    """Check for unread messages. Returns the count of unread messages."""
    try:
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])

        if not messages:
            logger.info("No new replies.")
            return 0

        logger.info(f"🔔 {len(messages)} unread reply(s) found!")
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            logger.info(f"  From: {sender}  |  Subject: {subject}")

        return len(messages)
    except Exception as e:
        logger.error(f"Failed to check inbox: {e}")
        return -1


RESULT_FILE = "inbox_result.json"


def _write_result(payload):
    """Record the pass outcome so the daily report can state a real number."""
    import json

    try:
        with open(RESULT_FILE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
    except OSError as exc:
        logger.warning(f"Could not record the inbox result: {exc}")


def read_result():
    """The last recorded inbox pass, or None if the mailbox was never reached."""
    import json

    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def single_pass():
    """Run a single inbox check and exit. Used by the pipeline."""
    import datetime as _dt

    logger.info("Inbox Monitor: single-pass mode")
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    creds = authenticate_gmail()
    if not creds:
        _write_result({"ok": False, "unread": None, "checked_at": now,
                       "error": "could not authenticate to the mailbox"})
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)
        count = check_inbox(service)
        _write_result({"ok": count >= 0, "unread": count if count >= 0 else None,
                       "checked_at": now})
        return count >= 0
    except Exception as e:
        logger.error(f"Gmail API error: {e}")
        _write_result({"ok": False, "unread": None, "checked_at": now, "error": str(e)})
        return False


def continuous_loop():
    """Run continuous inbox polling (every 30 seconds). Used for direct execution."""
    logger.info("Inbox Monitor: continuous polling mode (Ctrl+C to stop)")
    creds = authenticate_gmail()
    if not creds:
        return

    service = build('gmail', 'v1', credentials=creds)
    logger.info("Connected to Gmail inbox. Monitoring for replies...")

    try:
        while True:
            check_inbox(service)
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Stopped Inbox Monitor.")


if __name__ == '__main__':
    if '--loop' in sys.argv:
        continuous_loop()
    else:
        # Exit non-zero so the pipeline cannot report [PASS] for a pass that
        # never reached the mailbox.
        raise SystemExit(0 if single_pass() else 1)
