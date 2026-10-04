"""Tests for the generated project's self-contained scripts/check.py."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("startai", os.path.join(REPO_ROOT, "scripts", "startai.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestCheckPy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "proj")
        m.scaffold(self.target, m.load_defaults())

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self):
        return subprocess.run(
            [sys.executable, os.path.join(self.target, "scripts", "check.py")],
            capture_output=True, text=True)

    def test_check_passes_on_fresh_scaffold(self):
        r = self._run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_check_detects_unresolved_token(self):
        with open(os.path.join(self.target, "README.md"), "a", encoding="utf-8") as f:
            f.write("\n{{unresolved}}\n")
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unresolved", r.stderr)

    def test_check_detects_empty_config_value(self):
        with open(os.path.join(self.target, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"product_name": "X", "email": ""}, f)
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("email", r.stderr)

    def test_check_detects_bilingual_mismatch(self):
        os.remove(os.path.join(self.target, "docs", "es", "signing.md"))
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("signing.md", r.stderr)

    def test_check_rejects_invalid_visibility_in_config(self):
        with open(os.path.join(self.target, "config.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"product_name": "X",
                       "ai_files_visibility": "pubic"}, f)
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ai_files_visibility", r.stderr)

    def test_check_rejects_invalid_visibility_in_manifest(self):
        with open(os.path.join(self.target, ".startai-adopt.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"ai_files_visibility": "pubic"}, f)
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ai_files_visibility", r.stderr)


if __name__ == "__main__":
    unittest.main()
