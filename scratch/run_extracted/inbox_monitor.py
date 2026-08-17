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
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Gmail token refreshed successfully.")
            except Exception as e:
                logger.error(f"Gmail token refresh failed: {e}")
                logger.error("ACTION REQUIRED: Re-run this script locally (with a browser) to re-authorize.")
                return None
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


def single_pass():
    """Run a single inbox check and exit. Used by the pipeline."""
    logger.info("Inbox Monitor: single-pass mode")
    creds = authenticate_gmail()
    if not creds:
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)
        count = check_inbox(service)
        return count >= 0
    except Exception as e:
        logger.error(f"Gmail API error: {e}")
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
        single_pass()
