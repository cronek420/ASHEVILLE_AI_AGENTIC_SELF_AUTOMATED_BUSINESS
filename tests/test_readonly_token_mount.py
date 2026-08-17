"""
Under Cloud Run the OAuth tokens are mounted from Secret Manager, so their paths
are read-only. Refreshing an expired token therefore succeeds in memory but
cannot be written back.

Every cloud pipeline run between 2026-08-07 and 2026-08-09 treated that write
failure as an auth failure and abandoned the session, so no run synced a sheet
or read the mailbox — while still reporting [PASS], because the entry points
discarded the return value. These tests pin both halves of the fix.
"""

import builtins
import sys
import unittest
from unittest import mock

import agency_auth
import inbox_monitor


def _expired_creds(refresh_ok=True):
    """A credential that is expired but holds a usable refresh token."""
    creds = mock.MagicMock()
    creds.valid = False
    creds.expired = True
    creds.refresh_token = "refresh-token"
    creds.to_json.return_value = '{"token": "refreshed"}'

    def refresh(_request):
        if not refresh_ok:
            raise RuntimeError("invalid_grant: token has been revoked")
        creds.valid = True
        creds.expired = False

    creds.refresh.side_effect = refresh
    return creds


class ReadOnlyTokenMountTests(unittest.TestCase):
    """A read-only token store must not cost us a working session."""

    def _authenticate(self, creds, open_error=None):
        real_open = builtins.open

        def fake_open(path, mode="r", *args, **kwargs):
            if "w" in mode and open_error is not None:
                raise open_error
            return real_open(path, mode, *args, **kwargs)

        with mock.patch.object(inbox_monitor.os.path, "exists", return_value=True), \
             mock.patch.object(inbox_monitor.Credentials, "from_authorized_user_file",
                               return_value=creds), \
             mock.patch.object(builtins, "open", side_effect=fake_open):
            return inbox_monitor.authenticate_gmail()

    def test_readonly_mount_still_yields_usable_credentials(self):
        creds = _expired_creds()
        result = self._authenticate(
            creds, open_error=OSError(30, "Read-only file system"))
        self.assertIsNotNone(
            result, "a failed token cache write must not discard a good refresh")
        self.assertTrue(result.valid)
        creds.refresh.assert_called_once()

    def test_writable_store_still_caches_the_token(self):
        creds = _expired_creds()
        written = {}

        real_open = builtins.open

        def capture_open(path, mode="r", *args, **kwargs):
            if "w" in mode:
                handle = mock.MagicMock()
                handle.__enter__.return_value = handle
                handle.write.side_effect = lambda text: written.setdefault(path, text)
                return handle
            return real_open(path, mode, *args, **kwargs)

        with mock.patch.object(inbox_monitor.os.path, "exists", return_value=True), \
             mock.patch.object(inbox_monitor.Credentials, "from_authorized_user_file",
                               return_value=creds), \
             mock.patch.object(builtins, "open", side_effect=capture_open):
            result = inbox_monitor.authenticate_gmail()

        self.assertIsNotNone(result)
        self.assertEqual(list(written.values()), ['{"token": "refreshed"}'])

    def test_a_genuine_refresh_failure_still_fails_closed(self):
        """Only the cache write is best effort. A revoked token must return None."""
        creds = _expired_creds(refresh_ok=False)
        self.assertIsNone(self._authenticate(creds))

    def test_no_refresh_token_still_fails_closed(self):
        creds = mock.MagicMock()
        creds.valid = False
        creds.expired = True
        creds.refresh_token = None
        self.assertIsNone(self._authenticate(creds))


class ExitCodeTests(unittest.TestCase):
    """A step that did no work must not be able to report success."""

    def test_single_pass_reports_failure_when_auth_returns_nothing(self):
        with mock.patch.object(inbox_monitor, "authenticate_gmail", return_value=None):
            self.assertFalse(inbox_monitor.single_pass())

    def test_entry_points_propagate_their_result(self):
        """The __main__ blocks must translate a False result into a non-zero exit."""
        import ast
        import pathlib

        for module in ["inbox_monitor.py", "live_sheets_sync.py"]:
            source = pathlib.Path(module).read_text(encoding="utf-8")
            tree = ast.parse(source)
            main_blocks = [
                node for node in tree.body
                if isinstance(node, ast.If) and "__main__" in ast.dump(node.test)
            ]
            self.assertTrue(main_blocks, f"{module} has no __main__ block")
            body = ast.dump(main_blocks[0])
            self.assertIn("SystemExit", body,
                          f"{module} ignores its own result, so a failed run exits 0")


class ServiceAccountFallbackTests(unittest.TestCase):
    """
    Sheets and Drive are not Cloud Platform APIs, so the metadata server can
    return a token whose scopes do not cover them. That failure appears on the
    first real call, so a bad job identity must degrade to the OAuth token
    rather than lose the run.
    """

    def setUp(self):
        self.fake_gspread = mock.MagicMock()
        self.addCleanup(sys.modules.pop, "gspread", None)
        sys.modules["gspread"] = self.fake_gspread

    def _client(self, probe_error=None, in_cloud=True):
        adc = mock.MagicMock(name="adc-credentials")
        oauth = mock.MagicMock(name="oauth-credentials")
        clients = {}

        def authorize(creds):
            client = mock.MagicMock(name=f"client-for-{creds._mock_name}")
            if creds is adc and probe_error is not None:
                client.open_by_key.side_effect = probe_error
            clients[creds._mock_name] = client
            return client

        self.fake_gspread.authorize.side_effect = authorize

        with mock.patch.object(agency_auth, "running_in_cloud_run", return_value=in_cloud), \
             mock.patch.object(agency_auth, "adc_credentials", return_value=adc), \
             mock.patch.object(agency_auth, "oauth_credentials", return_value=oauth):
            client = agency_auth.sheets_client(verbose=False, probe_spreadsheet_id="SHEET_1")

        return client, clients

    def test_job_identity_is_used_when_it_can_reach_sheets(self):
        client, clients = self._client()
        self.assertIs(client, clients["adc-credentials"])
        self.assertNotIn("oauth-credentials", clients)

    def test_scope_failure_falls_back_to_oauth(self):
        client, clients = self._client(probe_error=PermissionError("insufficient scopes"))
        self.assertIs(client, clients["oauth-credentials"],
                      "a job identity that cannot reach Sheets must not lose the run")

    def test_probe_actually_touches_the_target_spreadsheet(self):
        _client, clients = self._client()
        clients["adc-credentials"].open_by_key.assert_called_once_with("SHEET_1")

    def test_outside_cloud_run_the_job_identity_is_never_tried(self):
        _client, clients = self._client(in_cloud=False)
        self.assertNotIn("adc-credentials", clients)


if __name__ == "__main__":
    unittest.main()
