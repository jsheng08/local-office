import unittest
from datetime import date

from services.agents.finance import claims


class FinanceTests(unittest.TestCase):
    def receipt(self, **changes):
        fields = dict(vendor="Synthetic cafe", date="2026-10-10", currency="MYR",
                      total_amount=40, category="meal", confidence="high")
        fields.update(changes)
        return claims.ReceiptExtraction(**fields)

    def check(self, **changes):
        return claims.policy_checks(self.receipt(**changes), today=date(2026, 10, 17))

    def test_meal_over_limit_fails_ex2(self):
        checks, _ = self.check(total_amount=85)
        self.assertTrue(any(c["rule"] == "EX-2" and not c["passed"]
                            and "exceeds" in c["detail"] and "60" in c["detail"] for c in checks))

    def test_client_entertainment_within_limit_needs_pm_preapproval(self):
        checks, _ = self.check(category="client_entertainment", total_amount=178.08)
        self.assertTrue(any(c["rule"] == "EX-2" and c["passed"]
                            and "within limit RM 200" in c["detail"] for c in checks))
        self.assertTrue(any(not c["passed"] and "PM pre-approval" in c["detail"] for c in checks))

    def test_non_myr_needs_review(self):
        checks, needs_review = self.check(currency="USD")
        self.assertTrue(needs_review)
        self.assertTrue(any(c["rule"] == "EX-2" and not c["passed"]
                            and "currency USD" in c["detail"] for c in checks))

    def test_future_date_fails_ex1(self):
        checks, _ = self.check(date="2026-10-18")
        self.assertTrue(any(c["rule"] == "EX-1" and not c["passed"]
                            and "future" in c["detail"] for c in checks))

    def test_demo_file_path_traversal_rejected(self):
        for name in ("../receipt_grab_001.png", "..\\receipt_grab_001.png", "/tmp/receipt.png"):
            with self.subTest(name=name), self.assertRaises(claims.ClaimError) as caught:
                claims.load_demo_file(name)
            self.assertEqual(caught.exception.status, 400)
