import unittest

import master_dashboard


TENANTS = {
    "asheville": {"location": "Asheville NC", "spreadsheet_id": "SHEET_A"},
    "charlotte": {"location": "Charlotte NC", "spreadsheet_id": "SHEET_C"},
}


class BuildRowsTests(unittest.TestCase):
    def test_one_row_per_city_plus_header_and_total(self):
        rows = master_dashboard.build_rows(TENANTS)
        self.assertEqual(rows[0], master_dashboard.HEADERS)
        self.assertEqual(rows[1][0], "Asheville NC")
        self.assertEqual(rows[2][0], "Charlotte NC")
        self.assertEqual(rows[-1][0], "TOTAL")
        self.assertEqual(len(rows), 4)

    def test_each_city_pulls_from_its_own_workbook(self):
        rows = master_dashboard.build_rows(TENANTS)
        self.assertIn("SHEET_A", rows[1][1])
        self.assertNotIn("SHEET_C", " ".join(rows[1]))
        self.assertIn("SHEET_C", rows[2][1])
        self.assertNotIn("SHEET_A", " ".join(rows[2]))

    def test_scales_to_any_number_of_cities(self):
        many = {
            f"city{n}": {"location": f"City {n}", "spreadsheet_id": f"SHEET_{n}"}
            for n in range(12)
        }
        rows = master_dashboard.build_rows(many)
        self.assertEqual(len(rows), 14)  # header + 12 cities + total
        self.assertTrue(rows[-1][1].startswith("=SUM(B2:B13)"))

    def test_city_without_a_spreadsheet_is_skipped(self):
        rows = master_dashboard.build_rows({
            "good": {"location": "Good NC", "spreadsheet_id": "SHEET_G"},
            "pending": {"location": "Pending NC"},
        })
        labels = [row[0] for row in rows]
        self.assertIn("Good NC", labels)
        self.assertNotIn("Pending NC", labels)

    def test_no_cities_yields_header_only(self):
        self.assertEqual(master_dashboard.build_rows({}), [master_dashboard.HEADERS])

    def test_counts_are_error_tolerant(self):
        """IMPORTRANGE returns #REF! until access is granted; the roll-up must
        show a placeholder rather than breaking every downstream SUM."""
        rows = master_dashboard.build_rows(TENANTS)
        for cell in rows[1][1:7]:
            self.assertTrue(cell.startswith("=IFERROR("), cell)


if __name__ == "__main__":
    unittest.main()
