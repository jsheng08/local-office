"""LIVE=1 .venv/bin/python -m unittest tests.integration.test_api_live -v.

Uses real local inference. Does not start/stop the server; API requests append audit entries.
"""
import os
import unittest

import httpx


@unittest.skipUnless(os.environ.get("LIVE") == "1", "Set LIVE=1 for the running API and real local models")
class LiveAPITests(unittest.TestCase):
    def setUp(self):
        self.client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=240, trust_env=False)
        self.addCleanup(self.client.close)

    def test_health_all_models_ok(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["models"], body)
        self.assertEqual({model["name"] for model in body["models"]}, {"lightning", "omni", "nano"}, body)
        self.assertTrue(all(model["ok"] for model in body["models"]), body)
        self.assertFalse(body["hosted_fallback"])

    def test_employee_executive_forbidden(self):
        response = self.client.get("/api/executive/variance", headers={"X-Demo-User": "haziq"})
        self.assertEqual(response.status_code, 403, response.text)

    def test_hr_executive_forbidden(self):
        response = self.client.get("/api/executive/variance", headers={"X-Demo-User": "hana"})
        self.assertEqual(response.status_code, 403, response.text)

    def test_exec_variance_has_no_unverified_numbers(self):
        response = self.client.get("/api/executive/variance", params={"month": "2026-09"},
                                   headers={"X-Demo-User": "siti"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["unverified_numbers"], [], response.text)

    def test_onboarding_leave_answer_cites_policy(self):
        response = self.client.post("/api/onboarding/ask", headers={"X-Demo-User": "aisyah"},
                                    json={"question": "How many days of annual leave do I get?"})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "answered", body)
        self.assertTrue(body["answer"].strip(), body)
        self.assertTrue(body["citations"], body)
        self.assertTrue(all(c["section_id"].startswith("LV-") for c in body["citations"]), body)

    def test_analyst_decision_forbidden_before_resource_lookup(self):
        response = self.client.post("/api/change_sets/x/decision", headers={"X-Demo-User": "aisyah"},
                                    json={"decision": "approve"})
        self.assertEqual(response.status_code, 403, response.text)
