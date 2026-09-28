"""End-to-end tests for `startai.py adopt` (adoption into existing projects)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import helpers

SCRIPT = helpers.SCRIPT_PATH
REPO_ROOT = helpers.REPO_ROOT
HAS_GIT = shutil.which("git") is not None


def snapshot(root):
    """{rel: sha256} of every file under root (to prove nothing was written)."""
    out = {}
    for r, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git" or True]
        for name in fs:
            p = os.path.join(r, name)
            rel = os.path.relpath(p, root)
            with open(p, "rb") as f:
                out[rel] = hashlib.sha256(f.read()).hexdigest()
    return out


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class AdoptFixture(unittest.TestCase):
    """Base fixture: an existing project in a TemporaryDirectory."""

    with_git = True

    def setUp(self):
        if self.with_git and not HAS_GIT:
            self.skipTest("git not available")
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "proj")
        os.makedirs(self.target)
        write(self.target, "package.json",
              json.dumps({"name": "toy-app", "version": "1.2.3"}))
        write(self.target, "main.py", "print('hi')\n")
        if self.with_git:
            subprocess.run(["git", "init", "-q"], cwd=self.target, check=True)
            subprocess.run(["git", "config", "user.email", "t@t"],
                           cwd=self.target, check=True)
            subprocess.run(["git", "config", "user.name", "T"],
                           cwd=self.target, check=True)
            subprocess.run(["git", "add", "-A"], cwd=self.target, check=True)
            subprocess.run(["git", "-c", "commit.gpgsign=false",
                            "commit", "-qm", "init"],
                           cwd=self.target, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args, cwd=None, input_text=None):
        return subprocess.run(
            [sys.executable, SCRIPT, "adopt", *args],
            cwd=cwd or REPO_ROOT,
            input=input_text,
            capture_output=True, text=True,
        )

    def _run_in_target(self, *args):
        return self._run(*args, cwd=self.target)


class TestAdoptBasics(AdoptFixture):
    def test_list_layers(self):
        r = self._run("--list-layers")
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("agents", "hooks", "audit", "docs", "distribution", "release"):
            self.assertIn(name, r.stdout)

    def test_every_collect_key_is_claimed_by_a_layer(self):
        mod = helpers.load_module()
        files = mod.collect(mod.load_defaults())
        self.assertEqual(mod.unassigned_paths(files), [])

    def test_report_writes_nothing_by_default(self):
        before = snapshot(self.target)
        r = self._run(self.target, "--infer-only")
        self.assertIn("Nothing written", r.stdout)
        self.assertEqual(snapshot(self.target), before)

    def test_apply_agents_creates_agent_files_only(self):
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        for rel in ("AGENTS.md", ".agents/skills/ai-native/SKILL.md", "llms.txt"):
            self.assertTrue(os.path.isfile(os.path.join(self.target, rel)), rel)
        self.assertFalse(os.path.exists(os.path.join(self.target, "README.md")))
        self.assertFalse(os.path.exists(os.path.join(self.target, "docs")))

    def test_conflict_writes_startai_new(self):
        write(self.target, "AGENTS.md", "my own rules\n")
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.target, "AGENTS.md")) as f:
            self.assertEqual(f.read(), "my own rules\n")
        self.assertTrue(os.path.isfile(
            os.path.join(self.target, "AGENTS.md.startai-new")))

    def test_overwrite_replaces_conflict(self):
        write(self.target, "AGENTS.md", "my own rules\n")
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--infer-only", "--overwrite")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.target, "AGENTS.md")) as f:
            self.assertNotEqual(f.read(), "my own rules\n")
        self.assertFalse(os.path.exists(
            os.path.join(self.target, "AGENTS.md.startai-new")))

    def test_second_apply_is_idempotent(self):
        a = ["--apply", "--layers", "agents", "--infer-only"]
        self.assertEqual(self._run(self.target, *a).returncode, 0)
        r = self._run(self.target, *a)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("current", r.stdout)
        leftovers = [p for p in snapshot(self.target) if ".startai-new" in p]
        self.assertEqual(leftovers, [])

    def test_gitignore_managed_block_is_idempotent(self):
        write(self.target, ".gitignore", "# my own stuff\nnode_modules/\n")
        a = ["--apply", "--layers", "agents", "--infer-only"]
        self.assertEqual(self._run(self.target, *a).returncode, 0)
        self.assertEqual(self._run(self.target, *a).returncode, 0)
        with open(os.path.join(self.target, ".gitignore")) as f:
            content = f.read()
        self.assertEqual(content.count("# >>> startai >>>"), 1)
        self.assertEqual(content.count("# <<< startai <<<"), 1)
        self.assertIn("# my own stuff", content)
        self.assertIn("node_modules/", content)

    def test_token_blocker_aborts_apply(self):
        write(self.target, "web.md", "jekyll uses {{foo}} here\n")
        r = self._run(self.target, "--apply", "--layers", "hooks",
                      "--infer-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("web.md", r.stdout + r.stderr)
        self.assertFalse(os.path.exists(
            os.path.join(self.target, "scripts", "check.py")))
        r2 = self._run(self.target, "--apply", "--layers", "hooks",
                       "--infer-only", "--force")
        self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
        self.assertTrue(os.path.isfile(
            os.path.join(self.target, "scripts", "check.py")))

    def test_existing_git_hook_is_a_blocker(self):
        hook = os.path.join(self.target, ".git", "hooks", "pre-commit")
        write(self.target, os.path.relpath(hook, self.target),
              "#!/bin/sh\necho mine\n")
        r = self._run(self.target, "--apply", "--layers", "hooks",
                      "--infer-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pre-commit", r.stdout + r.stderr)
        with open(hook) as f:
            self.assertEqual(f.read(), "#!/bin/sh\necho mine\n")

    def test_release_without_audit_is_a_blocker(self):
        r = self._run(self.target, "--layers", "release", "--infer-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("audit", r.stdout)

    def test_manifest_written_and_layers_union(self):
        a = ["--apply", "--infer-only"]
        self.assertEqual(self._run(self.target, *a).returncode, 0)
        mpath = os.path.join(self.target, ".startai-adopt.json")
        with open(mpath) as f:
            m1 = json.load(f)
        self.assertEqual(m1["layers"], ["agents"])
        self.assertIn("AGENTS.md", m1["files"])
        self.assertIn("sha256", m1["files"]["AGENTS.md"])
        r = self._run(self.target, "--apply", "--layers", "agents,hooks",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(mpath) as f:
            m2 = json.load(f)
        self.assertEqual(m2["layers"], ["agents", "hooks"])

    def test_manual_prints_commands_and_writes_nothing(self):
        before = snapshot(self.target)
        r = self._run(self.target, "--manual", "--layers", "agents,hooks")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("cp ", r.stdout)
        self.assertIn("install-hooks.sh", r.stdout)
        self.assertEqual(snapshot(self.target), before)

    def test_project_conf_comments_absent_entries(self):
        r = self._run(self.target, "--apply", "--layers", "audit",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        conf = os.path.join(self.target,
                            "scripts/dev/audit/profiles/project.conf")
        with open(conf) as f:
            content = f.read()
        self.assertIn("# adopt: absent in this repo", content)
        # README.md does not exist in the fixture -> its entry is commented
        self.assertIn('# "README.md:badge_version"', content)

    def test_hooks_only_still_covers_manifest_in_gitignore(self):
        # The managed .gitignore block applies with ANY layer: the manifest
        # must stay ignored or the adopted pre-commit would block commits.
        r = self._run(self.target, "--apply", "--layers", "hooks",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        gi = os.path.join(self.target, ".gitignore")
        self.assertTrue(os.path.isfile(gi))
        with open(gi) as f:
            self.assertIn(".startai-adopt.json", f.read())
        self.assertFalse(os.path.exists(
            os.path.join(self.target, ".devinignore")))

    def test_report_announces_gitignore_merge(self):
        write(self.target, ".gitignore", "node_modules/\n")
        r = self._run(self.target, "--report", "--infer-only")
        self.assertIn("merged", r.stdout)
        with open(os.path.join(self.target, ".gitignore")) as f:
            self.assertEqual(f.read(), "node_modules/\n")

    def test_report_never_runs_the_wizard(self):
        # No --config/--infer-only: stdin is empty; a wizard would EOFError.
        r = self._run(self.target, "--report", input_text="")
        self.assertIn("Preflight findings", r.stdout)
        self.assertIn("Nothing written", r.stdout)

    def test_default_target_is_cwd(self):
        r = self._run_in_target("--apply", "--layers", "agents", "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "AGENTS.md")))


class TestAdoptNoGit(AdoptFixture):
    """Same flow on a target without git — degraded but functional."""

    with_git = False

    def test_no_git_warns_but_applies(self):
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("not a git repository", r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "AGENTS.md")))


if __name__ == "__main__":
    unittest.main()
