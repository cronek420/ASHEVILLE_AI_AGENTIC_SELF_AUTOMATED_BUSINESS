"""
One place that decides how the agency authenticates to Google Sheets and Drive.

Why this exists
---------------
The pipeline used to authenticate everywhere as Tom's personal Google account
through a desktop-app OAuth refresh token. That is the wrong instrument for a
headless daily job:

  * refreshing a token requires writing it back, and under Cloud Run the token
    is a read-only Secret Manager mount, so the write fails;
  * re-authorizing needs a browser, which a Cloud Run job does not have;
  * the token is tied to a personal account, so unrelated security events
    (2-Step Verification toggled, an account recovery) can revoke it and stop
    the business overnight.

Between 2026-08-07 and 2026-08-09 that combination silently stopped every cloud
run from writing a single row, while the pipeline still reported success.

Cloud Run already has an identity of its own, so up there we use it: no token
file, nothing to refresh, nothing to expire. Locally there is no attached
service account, so the existing token.json flow stays exactly as it was.

What this requires
------------------
Sheets and Drive permissions come from *document sharing*, not project IAM, so
the job's service account must be an Editor on each Command Center workbook.
`grant_sheet_access.py` does that, and prints what it changed.
"""

import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Written by Cloud Run for jobs and services respectively.
CLOUD_RUN_ENV_VARS = ("CLOUD_RUN_JOB", "K_SERVICE")

LOCAL_TOKEN_PATH = "token.json"
MOUNTED_TOKEN_PATH = "/secrets/token/token.json"

# Which credential the last sheets_client() call actually used. Callers cannot
# reliably read this back off a gspread client, and a check that guesses the
# identity wrong is worse than one that reports nothing.
last_identity = "not yet authenticated"


def running_in_cloud_run():
    return any(os.getenv(name) for name in CLOUD_RUN_ENV_VARS)


def token_path():
    return MOUNTED_TOKEN_PATH if os.path.exists(MOUNTED_TOKEN_PATH) else LOCAL_TOKEN_PATH


def clear_stale_adc_pointer(verbose=True):
    """
    Drop GOOGLE_APPLICATION_CREDENTIALS when it points at a file that is absent.

    google.auth honours this variable ahead of the metadata server, and every
    Google client library goes through google.auth — Sheets, Drive, and
    Firestore alike. The mounted .env sets it to a `client_secret.json` path
    that does not exist inside the container, so ADC failed with a confusing
    "File client_secret.json was not found" instead of ever asking Cloud Run
    who it is.

    This was first patched for Sheets only. Firestore then failed the same way
    and the smoke test caught it, which is the argument for fixing it in one
    shared place rather than at each call site.

    Returns the removed value so a caller can restore it, or None.
    """
    override = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not override or os.path.exists(override):
        return None
    if verbose:
        print(f"  [AUTH] Ignoring GOOGLE_APPLICATION_CREDENTIALS={override} (missing file).")
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS")
    return override


def adc_credentials(verbose=True):
    """The attached service account, via Application Default Credentials."""
    import google.auth

    removed = clear_stale_adc_pointer(verbose=verbose)
    try:
        creds, _project = google.auth.default(scopes=SCOPES)
    finally:
        if removed:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = removed

    if verbose:
        email = getattr(creds, "service_account_email", None) or "attached identity"
        print(f"  [AUTH] Cloud Run: trying the job identity {email} (no token file).")
    return creds


def sheets_credentials(verbose=True):
    """
    Return credentials for Sheets and Drive.

    In Cloud Run: the attached service account. Anywhere else: the local OAuth
    token, refreshed if needed.

    Note that this does not prove the credentials can reach Sheets — see
    sheets_client(), which probes before committing to them.
    """
    if running_in_cloud_run():
        return adc_credentials(verbose=verbose)
    return oauth_credentials(verbose=verbose)


def oauth_credentials(verbose=True):
    """The local, browser-authorized path. Unchanged behaviour, kept for dev use."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    path = token_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Authorize locally with a browser first."
        )

    creds = Credentials.from_authorized_user_file(path, SCOPES)
    if creds.valid:
        return creds
    if not (creds.expired and creds.refresh_token):
        raise RuntimeError(
            "No valid OAuth token and no refresh token; re-authorize locally."
        )

    creds.refresh(Request())
    if verbose:
        print("  [AUTH] Token refreshed successfully.")
    # Caching the refreshed token is an optimization. The credentials above are
    # already valid, so a read-only token store must not fail the run.
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(creds.to_json())
    except OSError as persist_err:
        if verbose:
            print(f"  [AUTH] Refreshed token not cached to {path}: {persist_err}")
    return creds


def sheets_client(verbose=True, probe_spreadsheet_id=None):
    """
    An authorized gspread client, however we happen to be running.

    The service-account path is preferred in Cloud Run because it cannot expire
    and is not tied to a personal account. But Sheets and Drive are not Cloud
    Platform APIs, and the metadata server may hand back a token whose scopes do
    not cover them — which surfaces only on the first real call, not at
    credential construction. So when a probe id is supplied we make that call up
    front and fall back to the OAuth token if it fails.

    The fallback matters: the OAuth path is known to work, so a scope problem
    degrades to the previous behaviour instead of losing a day of syncing.
    """
    global last_identity
    import gspread

    if running_in_cloud_run():
        try:
            creds = adc_credentials(verbose=verbose)
            client = gspread.authorize(creds)
            if probe_spreadsheet_id:
                client.open_by_key(probe_spreadsheet_id)
            email = getattr(creds, "service_account_email", None)
            last_identity = f"job identity ({email})" if email else "the attached job identity"
            if verbose:
                print("  [AUTH] Job identity accepted by Sheets; no token file involved.")
            return client
        except Exception as exc:
            if verbose:
                print(f"  [AUTH] Job identity cannot reach Sheets ({exc}).")
                print("  [AUTH] Falling back to the OAuth token.")

    last_identity = "user OAuth token"
    return gspread.authorize(oauth_credentials(verbose=verbose))

def retry_api(func, *args, **kwargs):
    """Wrap gspread API calls to handle 429 quota errors with exponential backoff."""
    import time
    import gspread.exceptions
    max_retries = 3
    delay = 2.0
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            if getattr(e.response, "status_code", None) == 429 and attempt < max_retries:
                print(f"  [RETRY] 429 Quota Exceeded for {getattr(func, '__name__', 'API call')}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
