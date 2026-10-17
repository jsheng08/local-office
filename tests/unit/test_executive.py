import unittest

from services.agents.executive import variance


class ExecutiveTests(unittest.TestCase):
    def setUp(self):
        self.computed = variance.compute_variance("2026-09")

    def test_planted_labour_variance(self):
        row = next(r for r in self.computed["rows"]
                   if r["project_id"] == "PRJ-SPL" and r["category"].lower() == "labour")
        self.assertEqual(row["budget_myr"], 52000)
        self.assertEqual(row["actual_myr"], 61400)
        self.assertEqual(row["variance_myr"], 9400)
        self.assertEqual(row["variance_pct"], 18.1)
        self.assertTrue(row["flagged"])

    def test_invented_amount_is_unverified(self):
        narrative = variance.Narrative(summary="Revenue was RM 200,000.", drivers=[])
        self.assertIn("200,000", variance.unverified_numbers(narrative, self.computed))

    def test_computed_figures_are_verified(self):
        narrative = variance.Narrative(
            summary="September 2026 labour: RM 52,000 budget; RM 61,400 actual; RM 9,400 (18.1%) over.",
            drivers=[])
        self.assertEqual(variance.unverified_numbers(narrative, self.computed), [])
