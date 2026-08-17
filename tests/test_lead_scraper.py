import unittest

import lead_scraper


class FallbackTargetsTests(unittest.TestCase):
    """A city must never receive another city's leads. Charlotte's tracker was
    filled with Asheville businesses because one hardcoded list served everyone."""

    def test_asheville_keeps_its_builtin_list(self):
        targets = lead_scraper.fallback_targets_for("asheville", {"location": "Asheville NC"})
        self.assertEqual(len(targets), len(lead_scraper.ASHEVILLE_FALLBACK_TARGETS))

    def test_other_cities_get_nothing_by_default(self):
        for tenant in ["charlotte", "raleigh", "greenville"]:
            self.assertEqual(
                lead_scraper.fallback_targets_for(tenant, {"location": "Somewhere NC"}),
                [],
                f"{tenant} must not inherit another city's leads",
            )

    def test_configured_targets_are_used(self):
        config = {
            "location": "Charlotte NC",
            "fallback_targets": [
                {"domain": "clt-plumbing.com", "url": "https://clt-plumbing.com", "name": "CLT Plumbing"},
            ],
        }
        targets = lead_scraper.fallback_targets_for("charlotte", config)
        self.assertEqual([t["domain"] for t in targets], ["clt-plumbing.com"])

    def test_configured_targets_override_the_asheville_builtin(self):
        config = {"fallback_targets": [{"domain": "only.com", "url": "https://only.com", "name": "Only"}]}
        targets = lead_scraper.fallback_targets_for("asheville", config)
        self.assertEqual([t["domain"] for t in targets], ["only.com"])

    def test_missing_config_is_safe(self):
        self.assertEqual(lead_scraper.fallback_targets_for("newcity", None), [])

    def test_returned_list_is_a_copy(self):
        targets = lead_scraper.fallback_targets_for("asheville", {})
        targets.clear()
        self.assertTrue(lead_scraper.ASHEVILLE_FALLBACK_TARGETS)


if __name__ == "__main__":
    unittest.main()
