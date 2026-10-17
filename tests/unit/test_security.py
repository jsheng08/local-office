import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from services.security import audit, auth


class PermissionTests(unittest.TestCase):
    def test_analyst_cannot_approve(self):
        self.assertFalse(auth.has_perm({"role": "analyst"}, "proposal:approve"))
        with patch.object(audit, "record") as recorded:
            with self.assertRaises(HTTPException) as caught:
                auth.require("proposal:approve")({"username": "aisyah", "role": "analyst"})
            self.assertEqual(caught.exception.status_code, 403)
            self.assertEqual(recorded.call_args.args[3], "denied")

    def test_hr_cannot_view_executive(self):
        self.assertFalse(auth.has_perm({"role": "hr"}, "exec:view"))
        with patch.object(audit, "record"):
            with self.assertRaises(HTTPException) as caught:
                auth.require("exec:view")({"username": "hana", "role": "hr"})
            self.assertEqual(caught.exception.status_code, 403)


class AuditTests(unittest.TestCase):
    def setUp(self):
        if not hasattr(audit, "AUDIT_PATH") or not hasattr(audit, "_last_hash"):
            self.skipTest("Audit module does not expose a redirectable path and hash cache")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "audit.jsonl"
        for name, value in (("AUDIT_PATH", self.path), ("_last_hash", None)):
            patcher = patch.object(audit, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_pair(self):
        first = audit.record(None, "test.first", "test:1", "ok")
        second = audit.record(None, "test.second", "test:2", "denied")
        return first, second

    def test_hash_chain_and_newest_first(self):
        first, second = self.write_pair()
        entries, valid = audit.read()
        self.assertTrue(valid)
        self.assertEqual(first["prev_hash"], audit.GENESIS)
        self.assertEqual(second["prev_hash"], first["hash"])
        self.assertEqual([e["id"] for e in entries], [second["id"], first["id"]])

    def test_tampered_entry_invalidates_entire_chain_even_with_limit(self):
        self.write_pair()
        lines = self.path.read_text().splitlines()
        entry = json.loads(lines[0])
        entry["outcome"] = "tampered"
        lines[0] = json.dumps(entry)
        self.path.write_text("\n".join(lines) + "\n")
        entries, valid = audit.read(limit=1)
        self.assertEqual(len(entries), 1)
        self.assertFalse(valid)

    def test_deleted_first_entry_breaks_chain(self):
        self.write_pair()
        self.path.write_text(self.path.read_text().splitlines()[1] + "\n")
        self.assertFalse(audit.read()[1])
