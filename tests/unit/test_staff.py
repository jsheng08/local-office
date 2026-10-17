import os
import unittest
from datetime import date
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.routers.staff import router
from services.agents.triage.agent import active_leave, load_staff, rank_staff
from services.security.auth import load_users


class StaffTests(unittest.TestCase):
    def test_leave_window_inclusive(self):
        self.assertNotIn('S07', active_leave(date(2026, 10, 12)))
        self.assertIn('S07', active_leave(date(2026, 10, 13)))
        self.assertIn('S07', active_leave(date(2026, 10, 24)))
        self.assertNotIn('S07', active_leave(date(2026, 10, 25)))
        self.assertNotIn('S06', active_leave(date(2026, 10, 15)))
        self.assertIn('S06', active_leave(date(2026, 10, 16)))
        self.assertIn('S06', active_leave(date(2026, 10, 20)))
        self.assertNotIn('S06', active_leave(date(2026, 10, 21)))

    def test_env_today_and_triage_exclusion(self):
        staff = load_staff()
        with patch.dict(os.environ, {'LO_TODAY': '2026-10-17'}):
            self.assertEqual(set(active_leave()), {'S06', 'S07'})
            self.assertNotIn('S06', [s['staff_id'] for s in rank_staff(['security'], 16, staff)])
            self.assertEqual(rank_staff(['UAT'], 16, staff), [])
            self.assertIn('S03', [s['staff_id'] for s in rank_staff(['security'], 16, staff)])
        with patch.dict(os.environ, {'LO_TODAY': '2026-10-25'}):
            self.assertIn('S06', [s['staff_id'] for s in rank_staff(['security'], 16, staff)])
            self.assertIn('S07', [s['staff_id'] for s in rank_staff(['UAT'], 16, staff)])

    def test_all_demo_users_directory_without_cost(self):
        app = FastAPI(); app.include_router(router)
        with TestClient(app) as client, patch.dict(os.environ, {'LO_TODAY': '2026-10-17'}):
            self.assertEqual(client.get('/api/staff').status_code, 401)
            users = load_users(); self.assertEqual(len(users), 7)
            for user in users:
                response = client.get('/api/staff', headers={'X-Demo-User': user['username']})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json())
                for row in response.json():
                    self.assertEqual(set(row), {'id', 'name', 'role', 'projects', 'weekly_capacity_h', 'allocated_h', 'on_leave'})
                    self.assertNotIn('hourly_cost_myr', row)
                    self.assertEqual(row['on_leave'] is not None, row['id'] in {'S06', 'S07'})
