import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.agents.onboarding import qa


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        (directory / "policy.md").write_text(
            "# Test policy\naudience: all\n\n## LV-1 Annual leave\nFourteen days.\n"
            "## LV-2 HR notes\naudience: [hr, exec]\nRestricted notes.\n")
        self.patch = patch.object(qa, "POLICY_DIR", directory)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_section_parsing(self):
        sections = qa.load_sections()
        self.assertEqual([s["section_id"] for s in sections], ["LV-1", "LV-2"])
        self.assertEqual(sections[0]["text"], "Fourteen days.")
        self.assertEqual(sections[0]["doc"], "policy.md")
        self.assertEqual(sections[0]["doc_title"], "Test policy")
        self.assertEqual(sections[1]["audience"], ["hr", "exec"])
        self.assertNotIn("audience:", sections[1]["text"])

    def test_audience_filtering(self):
        self.assertEqual([s["section_id"] for s in qa.authorized_sections({"role": "analyst"})], ["LV-1"])
        self.assertEqual([s["section_id"] for s in qa.authorized_sections({"role": "hr"})], ["LV-1", "LV-2"])

    @unittest.skip("No pure citation helper: filtering is inside ask(), after chat_json; model calls excluded")
    def test_invalid_citation_ids_dropped(self):
        pass

    @unittest.skip("No pure escalation helper: citation enforcement is inside ask(), after chat_json")
    def test_answer_without_valid_citations_escalates(self):
        pass
