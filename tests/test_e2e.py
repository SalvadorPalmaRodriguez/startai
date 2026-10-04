"""End-to-end tests: run scripts/startai.py as a subprocess via the CLI."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import helpers

SCRIPT = helpers.SCRIPT_PATH
REPO_ROOT = helpers.REPO_ROOT


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "proj")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            cwd=REPO_ROOT,
            input=input_text,
            capture_output=True,
            text=True,
        )

    def _write_config(self, overrides=None):
        cfg = helpers.load_module().load_defaults()
        if overrides:
            cfg.update(overrides)
        path = os.path.join(self.tmp.name, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        return path

    def test_help_lists_options(self):
        r = self._run("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("--config", r.stdout)
        self.assertIn("--no-review", r.stdout)
        self.assertIn("--dry-run", r.stdout)
        self.assertIn("--dry-run-output", r.stdout)
        self.assertIn("--strict", r.stdout)

    def test_non_interactive_generates_project(self):
        cfg_path = self._write_config({
            "product_name": "My App",
            "github_user": "me",
            "repo": "my-repo",
        })
        r = self._run(self.target, "--config", cfg_path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "README.md")))
        with open(os.path.join(self.target, "README.md"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn("My App", content)
        self.assertIn("https://github.com/me/my-repo", content)
        # config.json persisted for reuse with --config
        self.assertTrue(os.path.isfile(os.path.join(self.target, "config.json")))

    def test_refuses_non_empty_target(self):
        os.makedirs(self.target)
        with open(os.path.join(self.target, "x.txt"), "w", encoding="utf-8") as f:
            f.write("occupied")
        cfg_path = self._write_config()
        r = self._run(self.target, "--config", cfg_path)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not empty", r.stdout + r.stderr)

    def test_interactive_wizard_accepts_defaults(self):
        # Feed empty lines to accept every default; --no-review skips the file review.
        r = self._run(self.target, "--no-review", input_text="\n" * 30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "README.md")))
        with open(os.path.join(self.target, "README.md"), encoding="utf-8") as f:
            with open(helpers.CONFIG_EXAMPLE, encoding="utf-8") as cfg_f:
                default_name = json.load(cfg_f)["product_name"]
            self.assertIn(default_name, f.read())

    def test_dry_run_does_not_create_files(self):
        cfg_path = self._write_config({"product_name": "Dry Run App"})
        target = os.path.join(self.tmp.name, "dry-proj")
        out = os.path.join(self.tmp.name, "preview.txt")
        r = self._run(target, "--config", cfg_path, "--dry-run", "--dry-run-output", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(target))
        self.assertIn("README.md", r.stdout)
        self.assertIn("Dry Run App", r.stdout)

    def test_dry_run_saves_preview_file(self):
        cfg_path = self._write_config({"product_name": "Preview App"})
        out = os.path.join(self.tmp.name, "preview.txt")
        r = self._run(self.target, "--config", cfg_path, "--dry-run", "--dry-run-output", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Preview App", content)
        self.assertIn("README.md", content)

    def test_strict_aborts_on_empty_value(self):
        cfg_path = self._write_config({"email": ""})
        r = self._run(self.target, "--config", cfg_path, "--strict")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("email", r.stderr)
        self.assertFalse(os.path.exists(self.target))

    def test_strict_passes_with_valid_config(self):
        cfg_path = self._write_config()
        out = os.path.join(self.tmp.name, "p.txt")
        r = self._run(self.target, "--config", cfg_path, "--strict", "--dry-run", "--dry-run-output", out)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_warns_on_empty_value(self):
        cfg_path = self._write_config({"email": ""})
        r = self._run(self.target, "--config", cfg_path, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING", r.stderr)
        self.assertIn("email", r.stderr)

    def test_check_passes(self):
        r = self._run("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("coherent", r.stdout)


if __name__ == "__main__":
    unittest.main()
