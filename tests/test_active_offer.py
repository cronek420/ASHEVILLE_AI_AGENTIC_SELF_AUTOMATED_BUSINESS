"""
The city sells the offer Tom picked in 'Start Here' — not a default.

Before this existed, proposal_engine chose per prospect from the audit's
`recommended_product`. Of 136 audited Asheville prospects, 132 would have been
quoted a $75 offer while the sheet said the active offer was $149. The control
cell did nothing.

The rule these tests defend: match confidently or refuse. A wrong match sends a
real business the wrong price, which is worse than sending nothing.
"""

import unittest
from unittest import mock

import active_offer

PRODUCTS = {
    "IDEA-01": {"name": "24-Hour Mobile Booking-Page Rescue", "total": 149,
                "deposit": 75, "desc": "mobile booking page rescue"},
    "IDEA-02": {"name": "Same-Day 3-CTA Repair", "total": 75,
                "deposit": 40, "desc": "same-day website and CTA repair"},
    "IDEA-03": {"name": "One-Offer Promo Sprint", "total": 99,
                "deposit": 50, "desc": "promotional content pack"},
    "IDEA-04": {"name": "Google Profile Accuracy Session", "total": 99,
                "deposit": 50, "desc": "Google Business Profile accuracy session"},
}


class MatchProductTests(unittest.TestCase):
    def test_exact_name_wins(self):
        self.assertEqual(
            active_offer.match_product("24-Hour Mobile Booking-Page Rescue", 149, PRODUCTS),
            "IDEA-01")

    def test_matching_ignores_case_and_punctuation(self):
        self.assertEqual(
            active_offer.match_product("24 hour mobile booking page rescue!", None, PRODUCTS),
            "IDEA-01")

    def test_description_resolves_a_renamed_offer(self):
        """Charlotte's real sheet value, which matches no product name."""
        self.assertEqual(
            active_offer.match_product("AI-Assisted Promotional Content Pack", 99, PRODUCTS),
            "IDEA-03")

    def test_price_alone_is_used_only_when_unambiguous(self):
        """Two products cost $99, so price must not decide between them."""
        self.assertIsNone(
            active_offer.match_product("Some Unrelated Offer Name", 99, PRODUCTS))

    def test_unique_price_can_resolve(self):
        self.assertEqual(
            active_offer.match_product("Totally Different Wording", 75, PRODUCTS),
            "IDEA-02")

    def test_an_unknown_offer_refuses_rather_than_defaulting(self):
        self.assertIsNone(
            active_offer.match_product("Underwater Basket Weaving", 500, PRODUCTS))

    def test_blank_offer_matches_nothing(self):
        self.assertIsNone(active_offer.match_product("", None, PRODUCTS))


class ResolveTests(unittest.TestCase):
    def test_unmatched_offer_raises_with_a_usable_message(self):
        with mock.patch.object(active_offer, "read_from_sheet",
                               return_value={"name": "Mystery Offer", "price": 500}), \
             mock.patch.object(active_offer, "save_cache"):
            with self.assertRaises(ValueError) as caught:
                active_offer.resolve("asheville", "SHEET", PRODUCTS)
        message = str(caught.exception)
        self.assertIn("Mystery Offer", message)
        self.assertIn("Same-Day 3-CTA Repair", message, "should list valid options")

    def test_a_failed_read_falls_back_to_cache_and_says_so(self):
        with mock.patch.object(active_offer, "read_from_sheet",
                               side_effect=RuntimeError("network down")), \
             mock.patch.object(active_offer, "load_cache",
                               return_value={"name": "One-Offer Promo Sprint", "price": 99}):
            pid, product, note = active_offer.resolve("charlotte", "SHEET", PRODUCTS)
        self.assertEqual(pid, "IDEA-03")
        self.assertIn("CACHED", note)

    def test_a_failed_read_with_no_cache_refuses(self):
        """Never invent an offer just because the sheet was unreachable."""
        with mock.patch.object(active_offer, "read_from_sheet",
                               side_effect=RuntimeError("network down")), \
             mock.patch.object(active_offer, "load_cache", return_value=None):
            with self.assertRaises(ValueError):
                active_offer.resolve("charlotte", "SHEET", PRODUCTS)

    def test_price_drift_between_sheet_and_product_is_reported(self):
        with mock.patch.object(active_offer, "read_from_sheet",
                               return_value={"name": "One-Offer Promo Sprint", "price": 129}), \
             mock.patch.object(active_offer, "save_cache"):
            _pid, product, note = active_offer.resolve("charlotte", "SHEET", PRODUCTS)
        self.assertIn("PRICE MISMATCH", note)
        self.assertEqual(product["total"], 99, "the product price is what gets charged")


if __name__ == "__main__":
    unittest.main()
