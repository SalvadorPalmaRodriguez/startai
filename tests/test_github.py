"""Unit tests for scripts/github.py (command construction, no network)."""
import importlib.util
import os
import subprocess
import unittest
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITHUB = os.path.join(REPO_ROOT, "scripts", "github.py")

spec = importlib.util.spec_from_file_location("github", GITHUB)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


class TestGithubCommands(unittest.TestCase):
    def test_pages_url(self):
        self.assertEqual(gh.pages_url("me", "repo"), "https://me.github.io/repo/")

    def test_pages_url_user_site_repo(self):
        # "owner.github.io" is served at the domain root, not under /repo/.
        self.assertEqual(gh.pages_url("me", "me.github.io"),
                         "https://me.github.io/")
        self.assertEqual(gh.pages_url("Me", "ME.github.io"),
                         "https://Me.github.io/")

    def test_warn_step_reports_failure(self):
        r = subprocess.CompletedProcess(["x"], 1, "", "boom")
        with mock.patch("builtins.print") as p:
            self.assertTrue(gh.warn_step(r, "doing x"))
        p.assert_called_once()
        self.assertIn("boom", p.call_args[0][0])

    def test_warn_step_ok(self):
        r = subprocess.CompletedProcess(["x"], 0, "", "")
        self.assertFalse(gh.warn_step(r, "doing x"))

    def test_create_repo_cmd_public(self):
        cmd = gh.create_repo_cmd("me", "repo", "Desc", True)
        self.assertEqual(cmd[:3], ["repo", "create", "me/repo"])
        self.assertIn("--public", cmd)
        self.assertIn("--description", cmd)
        self.assertIn("--homepage", cmd)
        self.assertIn("https://me.github.io/repo/", cmd)

    def test_create_repo_cmd_private_no_description(self):
        cmd = gh.create_repo_cmd("me", "repo", "", False)
        self.assertIn("--private", cmd)
        self.assertNotIn("--description", cmd)

    def test_set_topic_cmd(self):
        self.assertEqual(gh.set_topic_cmd("me", "repo", "cli"),
                         ["repo", "edit", "me/repo", "--add-topic", "cli"])

    def test_enable_pages_cmd(self):
        cmd = gh.enable_pages_cmd("me", "repo", "main", "/docs")
        self.assertEqual(cmd[0], "api")
        self.assertIn("repos/me/repo/pages", cmd)
        self.assertIn("source[branch]=main", cmd)
        self.assertIn("source[path]=/docs", cmd)

    def test_trigger_build_cmd(self):
        self.assertEqual(gh.trigger_build_cmd("me", "repo"),
                         ["api", "repos/me/repo/pages/builds", "-X", "POST"])

    def test_build_status_cmd(self):
        cmd = gh.build_status_cmd("me", "repo")
        self.assertIn("repos/me/repo/pages/builds", cmd)
        self.assertIn("--jq", cmd)


if __name__ == "__main__":
    unittest.main()
