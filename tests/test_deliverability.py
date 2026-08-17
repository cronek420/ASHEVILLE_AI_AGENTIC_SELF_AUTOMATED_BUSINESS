"""
Screening prospects before they cost an approval decision.

Both businesses this system emailed in August 2026 hard-bounced, and both were
detectable in advance: one publishes no MX record, the other publishes a null MX
(RFC 7505) that explicitly declares it accepts no mail.

The distinction these tests protect: "no mail route exists" is a stable fact and
may drop a prospect; "the server did not answer just now" is a snapshot and may
only warn. Getting that backwards either wastes Tom's attention or silently
discards real businesses.
"""

import unittest
from unittest import mock

import deliverability


class ClassificationTests(unittest.TestCase):
    def check(self, hosts, connects=True):
        with mock.patch.object(deliverability, "_mx_hosts", return_value=hosts), \
             mock.patch.object(deliverability, "_accepts_connection", return_value=connects):
            return deliverability.check_domain("example.com", use_cache=False)

    def test_no_mx_is_a_hard_fail(self):
        result = self.check([])
        self.assertEqual(result["status"], deliverability.NO_MX)
        self.assertTrue(deliverability.is_hard_fail(result))

    def test_reachable_mx_is_deliverable(self):
        result = self.check(["mx.example.com"], connects=True)
        self.assertEqual(result["status"], deliverability.DELIVERABLE)
        self.assertFalse(deliverability.is_hard_fail(result))
        self.assertEqual(deliverability.warning_for(result), "")

    def test_unreachable_mx_warns_but_does_not_drop_the_prospect(self):
        """A server can be briefly down; that is not proof the business is unreachable."""
        result = self.check(["mx.example.com"], connects=False)
        self.assertEqual(result["status"], deliverability.UNREACHABLE)
        self.assertFalse(deliverability.is_hard_fail(result))
        self.assertIn("may bounce", deliverability.warning_for(result))

    def test_a_failed_lookup_is_unknown_not_undeliverable(self):
        """Not being able to check is different from having checked and found nothing."""
        result = self.check(None)
        self.assertEqual(result["status"], deliverability.UNKNOWN)
        self.assertFalse(deliverability.is_hard_fail(result))
        self.assertIn("not verified", deliverability.warning_for(result))


class NullMxTests(unittest.TestCase):
    """RFC 7505: a single '.' exchange means the domain accepts no mail."""

    def _resolve_to(self, exchanges):
        records = []
        for index, exchange in enumerate(exchanges):
            record = mock.MagicMock()
            record.preference = index
            record.exchange = exchange
            records.append(record)

        resolver = mock.MagicMock()
        resolver.resolve.return_value = records
        module = mock.MagicMock()
        module.resolver.Resolver.return_value = resolver
        return module

    def test_null_mx_reads_as_no_mail_route(self):
        with mock.patch.dict("sys.modules", {"dns": self._resolve_to(["."]),
                                             "dns.resolver": mock.MagicMock()}):
            hosts = deliverability._mx_hosts("nomail.example")
        self.assertEqual(hosts, [], "a null MX must not be probed as a real host")

    def test_real_mx_is_returned(self):
        with mock.patch.dict("sys.modules", {"dns": self._resolve_to(["mx1.example.com."]),
                                             "dns.resolver": mock.MagicMock()}):
            hosts = deliverability._mx_hosts("example.com")
        self.assertEqual(hosts, ["mx1.example.com"])


class AddressHelperTests(unittest.TestCase):
    def test_domain_is_taken_from_the_last_at_sign(self):
        self.assertEqual(deliverability.domain_of("A.Person@Example.COM "), "example.com")

    def test_screen_uses_the_address_domain(self):
        with mock.patch.object(deliverability, "check_domain") as checker:
            deliverability.screen("owner@shop.com", use_cache=False)
        checker.assert_called_once_with("shop.com", use_cache=False)


if __name__ == "__main__":
    unittest.main()
