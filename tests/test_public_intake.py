import unittest

from intake_store import MemoryIntakeStore
from public_intake_api import create_app


ORIGIN = "https://universal-ai-workforce.gronekthomas.chatgpt.site"


class PublicIntakeTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryIntakeStore()
        self.app = create_app({
            "TESTING": True,
            "ALLOWED_WEBSITE_ORIGIN": ORIGIN,
            "INTAKE_HASH_KEY": "test-only-key",
            "ONBOARDING_REQUEST_RATE_LIMIT_PER_HOUR": 2,
        }, self.store)
        self.client = self.app.test_client()
        self.valid = {"name": "Jane Owner", "email": "jane@example.com", "startingPoint": "existing_business", "source": "universal-ai-workforce-website"}

    def post(self, payload=None, origin=ORIGIN):
        headers = {"Origin": origin} if origin is not None else {}
        return self.client.post("/v1/public/onboarding-requests", json=payload or self.valid, headers=headers)

    def test_valid_request_is_review_only_and_audited(self):
        response = self.post()
        self.assertEqual(response.status_code, 202)
        record = next(iter(self.store.requests.values()))
        self.assertEqual(record["status"], "NEEDS_OWNER_REVIEW")
        self.assertEqual(record["mode"], "DRY_RUN")
        self.assertFalse(record["externalActionTaken"])
        self.assertEqual(len(self.store.audit_events), 1)

    def test_invalid_request_creates_no_record(self):
        response = self.post({"name": "Jane"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.store.requests, {})

    def test_unapproved_or_missing_origin_is_rejected(self):
        self.assertEqual(self.post(origin="https://evil.example").status_code, 403)
        self.assertEqual(self.post(origin=None).status_code, 403)

    def test_duplicate_retry_is_idempotent(self):
        first = self.post()
        second = self.post()
        self.assertEqual(first.get_json()["requestId"], second.get_json()["requestId"])
        self.assertEqual(len(self.store.requests), 1)
        self.assertEqual(len(self.store.audit_events), 1)

    def test_rate_limit_fails_closed(self):
        for index in range(2):
            self.assertEqual(self.post(dict(self.valid, email=f"person{index}@example.com")).status_code, 202)
        self.assertEqual(self.post(dict(self.valid, email="third@example.com")).status_code, 429)

    def test_unexpected_fields_are_rejected(self):
        self.assertEqual(self.post(dict(self.valid, admin=True)).status_code, 400)


if __name__ == "__main__":
    unittest.main()
