"""Private onboarding intake stores; never writes Google Sheets."""

from __future__ import annotations

import copy
import datetime as dt
from typing import Any, Dict, Iterable, Protocol, Tuple


class RateLimitExceeded(Exception):
    """Raised when a privacy-preserving rate-limit key is exhausted."""


class IntakeStore(Protocol):
    def create_request(self, record: Dict[str, Any], rate_keys: Iterable[str], hourly_limit: int) -> Tuple[Dict[str, Any], bool]: ...
    def pending_requests(self, limit: int = 100) -> list[Dict[str, Any]]: ...
    def mark_queued(self, request_id: str) -> None: ...


def _hour_bucket(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y%m%d%H")


class MemoryIntakeStore:
    """Deterministic in-memory implementation used only by tests."""

    def __init__(self) -> None:
        self.requests: dict[str, Dict[str, Any]] = {}
        self.audit_events: list[Dict[str, Any]] = []
        self.counters: dict[str, int] = {}

    def create_request(self, record, rate_keys, hourly_limit):
        request_id = record["requestId"]
        if request_id in self.requests:
            return copy.deepcopy(self.requests[request_id]), False
        keys = [f"{_hour_bucket()}:{key}" for key in rate_keys]
        if any(self.counters.get(key, 0) >= hourly_limit for key in keys):
            raise RateLimitExceeded()
        for key in keys:
            self.counters[key] = self.counters.get(key, 0) + 1
        self.requests[request_id] = copy.deepcopy(record)
        self.audit_events.append({
            "eventType": "public_onboarding_request_received",
            "requestId": request_id,
            "recordedAt": record["submittedAt"],
            "externalActionTaken": False,
        })
        return copy.deepcopy(record), True

    def pending_requests(self, limit=100):
        pending = [r for r in self.requests.values() if r["status"] == "NEEDS_OWNER_REVIEW"]
        return copy.deepcopy(pending[:limit])

    def mark_queued(self, request_id):
        if request_id in self.requests:
            self.requests[request_id]["queueState"] = "STAGED_IN_APPROVAL_QUEUE"


class FirestoreIntakeStore:
    """Firestore-backed queue with transactional rate limits and audit creation."""

    def __init__(self, client=None, collection_prefix="workforce") -> None:
        if client is None:
            from google.cloud import firestore
            client = firestore.Client()
        self.client = client
        self.intakes = client.collection(f"{collection_prefix}_intake_requests")
        self.audits = client.collection(f"{collection_prefix}_audit_events")
        self.limits = client.collection(f"{collection_prefix}_rate_limits")

    def create_request(self, record, rate_keys, hourly_limit):
        from google.cloud import firestore
        request_ref = self.intakes.document(record["requestId"])
        audit_ref = self.audits.document(f"received_{record['requestId']}")
        counter_refs = [self.limits.document(f"{_hour_bucket()}_{key}") for key in rate_keys]
        transaction = self.client.transaction()

        @firestore.transactional
        def commit(txn):
            existing = request_ref.get(transaction=txn)
            if existing.exists:
                return existing.to_dict(), False
            snapshots = [ref.get(transaction=txn) for ref in counter_refs]
            if any((snap.to_dict() or {}).get("count", 0) >= hourly_limit for snap in snapshots):
                raise RateLimitExceeded()
            for ref, snap in zip(counter_refs, snapshots):
                txn.set(ref, {"count": (snap.to_dict() or {}).get("count", 0) + 1, "hourBucket": _hour_bucket()})
            txn.create(request_ref, record)
            txn.create(audit_ref, {
                "eventType": "public_onboarding_request_received",
                "requestId": record["requestId"],
                "recordedAt": record["submittedAt"],
                "externalActionTaken": False,
            })
            return record, True
        return commit(transaction)

    def pending_requests(self, limit=100):
        query = self.intakes.where("status", "==", "NEEDS_OWNER_REVIEW").limit(limit)
        return [snapshot.to_dict() for snapshot in query.stream()]

    def mark_queued(self, request_id):
        self.intakes.document(request_id).update({
            "queueState": "STAGED_IN_APPROVAL_QUEUE",
            "queuedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        })


def firestore_store_from_env():
    import os
    return FirestoreIntakeStore(collection_prefix=os.getenv("WORKFORCE_COLLECTION_PREFIX", "workforce"))
