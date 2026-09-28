"""Tests for the git hooks in scripts/git/."""
import os
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_DIR = os.path.join(REPO_ROOT, "scripts", "git")


class TestGitHooks(unittest.TestCase):
    def test_hook_files_exist_and_executable(self):
        for name in ("pre-commit", "pre-push", "commit-msg", "install-hooks.sh"):
            path = os.path.join(GIT_DIR, name)
            self.assertTrue(os.path.isfile(path), name)
            self.assertTrue(os.access(path, os.X_OK), f"not executable: {name}")

    def test_install_hooks_creates_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            os.makedirs(os.path.join(tmp, "scripts", "git"))
            for name in ("pre-commit", "pre-push", "commit-msg", "install-hooks.sh"):
                shutil.copy(os.path.join(GIT_DIR, name),
                            os.path.join(tmp, "scripts", "git", name))
                os.chmod(os.path.join(tmp, "scripts", "git", name), 0o755)
            r = subprocess.run(["bash", "scripts/git/install-hooks.sh"],
                               cwd=tmp, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for name in ("pre-commit", "pre-push", "commit-msg"):
                link = os.path.join(tmp, ".git", "hooks", name)
                self.assertTrue(os.path.islink(link), name)

    def test_commit_msg_rejects_ai_trailer(self):
        with tempfile.TemporaryDirectory() as tmp:
            msg = os.path.join(tmp, "msg.txt")
            with open(msg, "w", encoding="utf-8") as f:
                f.write("feat: add X\n\nCo-Authored-By: devin-ai-integration[bot]\n")
            r = subprocess.run(["bash", os.path.join(GIT_DIR, "commit-msg"), msg],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)

    def test_commit_msg_accepts_normal_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            msg = os.path.join(tmp, "msg.txt")
            with open(msg, "w", encoding="utf-8") as f:
                f.write("fix: correct a typo\n")
            r = subprocess.run(["bash", os.path.join(GIT_DIR, "commit-msg"), msg],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
