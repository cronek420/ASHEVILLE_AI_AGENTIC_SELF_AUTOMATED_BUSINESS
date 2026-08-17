"""
Durable record of who has been emailed, and who must never be emailed again.

Why this exists
---------------
email_dispatcher.py kept both facts in local files: sent_ledger.local.jsonl and
dnc.local.json. Under Cloud Run those paths are inside the container and are
destroyed when the execution ends, so a cloud dispatch would begin every run
with no memory of anyone it had already contacted. The same prospect could be
emailed day after day — the exact outcome the approval gates exist to prevent.

On 2026-08-09 neither file existed locally either, while bounce notices proved
two businesses had already been emailed on 2026-08-03/04. The record of real
outreach had simply evaporated.

This module keeps that state in Firestore, which already backs the intake queue,
and merges in the local files so a developer's machine still works offline.

Failure direction
-----------------
Every read is fail-closed. An empty ledger means "nobody has been contacted",
which reads as permission to send — so if the durable backend is configured but
unreachable, we raise LedgerUnavailable rather than return an empty set. The
dispatcher turns that into a refusal to send. Losing a day of outreach is
recoverable; emailing a prospect twice is not.
"""

import datetime as dt
import json
import os
from pathlib import Path

DEFAULT_LEDGER_FILE = Path("sent_ledger.local.jsonl")
DEFAULT_DNC_FILE = Path("dnc.local.json")
COLLECTION_PREFIX = os.getenv("WORKFORCE_COLLECTION_PREFIX", "workforce")


class LedgerUnavailable(Exception):
    """The durable record could not be read, so no send may be authorized."""


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _normalize(value):
    return str(value or "").strip().lower()


def dnc_entries(raw):
    """
    Accept both shapes of suppression file.

    The original format was a flat list of strings. Entries may now also be
    objects carrying the reason and provenance, because "why is this address
    blocked" is exactly what you want when reviewing the list months later.
    """
    values = set()
    for item in raw or []:
        if isinstance(item, dict):
            candidate = item.get("address") or item.get("domain") or ""
        else:
            candidate = item
        candidate = _normalize(candidate)
        if candidate:
            values.add(candidate)
    return values


class OutreachLedger:
    """
    Merged view over Firestore and the local files.

    A send recorded in either place counts as sent. A suppression recorded in
    either place blocks. Merging in that direction is deliberate: both errors it
    can make are the safe kind — refusing to send, never sending twice.
    """

    def __init__(self, firestore_client=None, ledger_file=DEFAULT_LEDGER_FILE,
                 dnc_file=DEFAULT_DNC_FILE, require_durable=None, use_firestore=None,
                 collection_prefix=COLLECTION_PREFIX):
        self.ledger_file = Path(ledger_file)
        self.dnc_file = Path(dnc_file)
        self.collection_prefix = collection_prefix
        self._client = firestore_client
        self._client_attempted = firestore_client is not None
        in_cloud_run = bool(os.getenv("CLOUD_RUN_JOB") or os.getenv("K_SERVICE"))
        # In Cloud Run the local files cannot persist, so Firestore is not
        # optional there. Locally it is a bonus.
        if require_durable is None:
            require_durable = in_cloud_run
        # Reaching Firestore is a network call, so it is never incidental:
        # unasked-for calls made the test suite a hundred times slower and had
        # it reading production data. Callers that want durability say so.
        if use_firestore is None:
            use_firestore = in_cloud_run or firestore_client is not None
        self.require_durable = require_durable
        self.use_firestore = use_firestore

    # -- backend ---------------------------------------------------------

    def client(self):
        if not self.use_firestore:
            return None
        if not self._client_attempted:
            self._client_attempted = True
            try:
                from google.cloud import firestore

                # Firestore resolves credentials through google.auth too, so the
                # same stale GOOGLE_APPLICATION_CREDENTIALS pointer that broke
                # Sheets also breaks the ledger. Clear it before connecting.
                import agency_auth

                removed = agency_auth.clear_stale_adc_pointer(verbose=False)
                try:
                    self._client = firestore.Client()
                finally:
                    if removed:
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = removed
            except Exception as exc:
                self._client = None
                self._client_error = exc
        return self._client

    def _require(self, operation):
        """Raise when durability is mandatory but the backend is missing."""
        if self.require_durable and self.client() is None:
            raise LedgerUnavailable(
                f"Firestore is unavailable, so {operation} cannot be trusted: "
                f"{getattr(self, '_client_error', 'no client')}"
            )

    def _sends(self):
        return self.client().collection(f"{self.collection_prefix}_outreach_sends")

    def _suppressions(self):
        return self.client().collection(f"{self.collection_prefix}_outreach_suppressions")

    # -- reads -----------------------------------------------------------

    def sent_hashes(self):
        """Every message hash known to have been delivered to someone."""
        self._require("the duplicate-send guard")
        hashes = set()

        if self.ledger_file.exists():
            with self.ledger_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        hashes.add(json.loads(line)["message_sha256"])
                    except (json.JSONDecodeError, KeyError):
                        continue

        if self.client() is not None:
            try:
                for snapshot in self._sends().stream():
                    digest = (snapshot.to_dict() or {}).get("message_sha256")
                    if digest:
                        hashes.add(digest)
            except Exception as exc:
                raise LedgerUnavailable(f"could not read sent records: {exc}")
        return hashes

    def sent_recipients(self):
        """Addresses already contacted, whatever the message was."""
        self._require("the duplicate-send guard")
        recipients = set()

        if self.ledger_file.exists():
            with self.ledger_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        recipients.add(_normalize(json.loads(line).get("recipient")))
                    except json.JSONDecodeError:
                        continue

        if self.client() is not None:
            try:
                for snapshot in self._sends().stream():
                    recipients.add(_normalize((snapshot.to_dict() or {}).get("recipient")))
            except Exception as exc:
                raise LedgerUnavailable(f"could not read sent records: {exc}")
        return {r for r in recipients if r}

    def suppressed(self):
        """Addresses and domains that must not be contacted."""
        self._require("the suppression list")
        values = set()

        if self.dnc_file.exists():
            try:
                with self.dnc_file.open("r", encoding="utf-8") as handle:
                    values |= dnc_entries(json.load(handle))
            except json.JSONDecodeError as exc:
                # A malformed suppression file must never read as "nobody is
                # suppressed"; that silently unblocks everyone on it.
                raise LedgerUnavailable(f"{self.dnc_file} is not valid JSON: {exc}")

        if self.client() is not None:
            try:
                for snapshot in self._suppressions().stream():
                    record = snapshot.to_dict() or {}
                    value = _normalize(record.get("address") or record.get("domain"))
                    if value:
                        values.add(value)
            except Exception as exc:
                raise LedgerUnavailable(f"could not read suppressions: {exc}")
        return values

    # -- writes ----------------------------------------------------------

    def record_send(self, recipient, domain, message_sha256, timestamp=None, note=""):
        """
        Record a delivered message. Raises if it cannot be recorded durably.

        The caller must stop sending on failure: an unrecorded send is
        indistinguishable from one that never happened, which is how the same
        prospect gets contacted twice.
        """
        entry = {
            "timestamp": timestamp or _now(),
            "recipient": _normalize(recipient),
            "domain": _normalize(domain),
            "message_sha256": message_sha256,
        }
        if note:
            entry["note"] = note

        wrote_durably = False
        if self.client() is not None:
            try:
                self._sends().document(message_sha256).set(entry)
                wrote_durably = True
            except Exception as exc:
                if self.require_durable:
                    raise LedgerUnavailable(f"could not record the send: {exc}")

        if self.require_durable and not wrote_durably:
            raise LedgerUnavailable("no durable backend accepted the send record")

        try:
            with self.ledger_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        except OSError:
            # Read-only or absent local disk is fine once the durable write won.
            if not wrote_durably:
                raise
        return entry

    def suppress(self, address, reason="", source="", added=None):
        """Add an address to the do-not-contact list, durably where possible."""
        value = _normalize(address)
        if not value:
            raise ValueError("an empty address cannot be suppressed")
        record = {
            "address": value,
            "reason": reason,
            "source": source,
            "added": added or _now(),
        }
        if self.client() is not None:
            self._suppressions().document(value.replace("/", "_")).set(record)
        return record
