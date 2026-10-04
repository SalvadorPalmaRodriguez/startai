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

    def test_token_scan_skips_adopted_check_py(self):
        # The adopted scripts/check.py contains "{YYYY-MM-DD}" inside its
        # own LEGACY_TOKEN_RE — a re-adopt must not flag it (the file is
        # already in check.py's own SKIP_TOKEN_FILES).
        r = self._run(self.target, "--apply", "--layers", "hooks",
                      "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        r2 = self._run(self.target, "--apply", "--layers", "hooks",
                       "--infer-only")
        self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
        self.assertNotIn("check.py would reject", r2.stdout + r2.stderr)
        # user files with real tokens are still flagged
        write(self.target, "page.md", "has {{token}} inside\n")
        r3 = self._run(self.target, "--layers", "hooks", "--infer-only")
        self.assertIn("page.md", r3.stdout + r3.stderr)

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

    def test_empty_layers_is_usage_error(self):
        r = self._run(self.target, "--layers", "", "--infer-only")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no layers selected", r.stderr)

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


class TestAdoptVisibility(AdoptFixture):
    """ai_files_visibility through adopt: resolution, doctor, flips."""

    def _write_config(self, **over):
        cfg = helpers.load_module().load_defaults()
        cfg.update(over)
        path = os.path.join(self.tmp.name, "cfg.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        return path

    def _track(self, *rels):
        for rel in rels:
            write(self.target, rel, "tracked\n")
        subprocess.run(["git", "add", "-A"], cwd=self.target, check=True)
        subprocess.run(["git", "-c", "commit.gpgsign=false",
                        "commit", "-qm", "track"], cwd=self.target, check=True)

    def test_invalid_flag_is_fatal(self):
        cfg = self._write_config(ai_files_visibility="pubic")
        for args in ((self.target, "--layers", "agents", "--config", cfg),
                     (self.target, "--manual", "--config", cfg),
                     (self.target, "--emit-dir", os.path.join(self.tmp.name, "out"),
                      "--config", cfg, "--infer-only")):
            r = self._run(*args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertIn("ai_files_visibility", r.stderr + r.stdout)
        # scaffold entrypoint too
        r = subprocess.run([sys.executable, SCRIPT,
                            os.path.join(self.tmp.name, "newproj"),
                            "--config", cfg],
                           cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ai_files_visibility", r.stderr)

    def test_public_report_no_blocker_for_tracked_ai(self):
        self._track("AGENTS.md", ".agents/README.md", "CLAUDE.md")
        cfg = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--layers", "hooks", "--config", cfg)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertNotIn("BLOCKER", r.stdout)

    def test_private_blocker_mentions_git_rm_cached_and_history(self):
        self._track("AGENTS.md", ".agents/README.md")
        cfg = self._write_config(ai_files_visibility="private")
        r = self._run(self.target, "--layers", "hooks", "--config", cfg)
        self.assertNotEqual(r.returncode, 0)
        out = r.stdout + r.stderr
        self.assertIn("git rm --cached", out)
        self.assertIn("history", out)

    def test_manifest_persists_flag(self):
        cfg = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--config", cfg)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.target, ".startai-adopt.json")) as f:
            manifest = json.load(f)
        self.assertEqual(manifest["ai_files_visibility"], "public")
        # public render: managed .gitignore block without AI patterns
        with open(os.path.join(self.target, ".gitignore")) as f:
            self.assertNotIn("**/AGENTS.md", f.read())

    def test_flip_to_public_without_layers_warns(self):
        # First adopt in private mode, then flip config to public with only
        # the agents layer selected -> warning, not blocker.
        cfg_priv = self._write_config(ai_files_visibility="private")
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--config", cfg_priv)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        cfg_pub = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--layers", "agents", "--config", cfg_pub)
        self.assertIn("ai_files_visibility", r.stdout)
        self.assertIn("WARN", r.stdout)
        self.assertNotIn("BLOCKER", r.stdout)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_flip_to_private_without_layers_blocks(self):
        cfg_pub = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--apply", "--layers", "agents",
                      "--config", cfg_pub)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        cfg_priv = self._write_config(ai_files_visibility="private")
        r = self._run(self.target, "--layers", "agents", "--config", cfg_priv)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ai_files_visibility", r.stdout)
        self.assertIn("BLOCKER", r.stdout)
        self.assertIn("git rm --cached", r.stdout)

    def test_flip_with_all_enforcement_layers_applies(self):
        cfg_priv = self._write_config(ai_files_visibility="private")
        r = self._run(self.target, "--apply",
                      "--layers", "agents,hooks,audit",
                      "--config", cfg_priv)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.target, ".gitignore")) as f:
            self.assertIn("**/AGENTS.md", f.read())
        cfg_pub = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--apply",
                      "--layers", "agents,hooks,audit",
                      "--config", cfg_pub)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.target, ".gitignore")) as f:
            self.assertNotIn("**/AGENTS.md", f.read())
        with open(os.path.join(self.target, ".startai-adopt.json")) as f:
            self.assertEqual(json.load(f)["ai_files_visibility"], "public")

    def test_emit_dir_public_arrays_drop_ai_entries(self):
        import re as _re
        out_dir = os.path.join(self.tmp.name, "emit")
        cfg_pub = self._write_config(ai_files_visibility="public")
        r = self._run(self.target, "--layers", "hooks,audit",
                      "--emit-dir", out_dir, "--config", cfg_pub)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        array_re = _re.compile(
            r"(PRIVATE_GLOBS|REQUIRED_GITIGNORE)=\((.*?)\)", _re.S)
        hook = os.path.join(out_dir, "scripts/git/pre-commit")
        conf = os.path.join(
            out_dir, "scripts/dev/audit/profiles/project.conf")
        for path in (hook, conf):
            with open(path) as f:
                text = f.read()
            self.assertNotIn("startai:", text, path)
            bodies = "\n".join(b for _, b in array_re.findall(text))
            self.assertTrue(bodies.strip(), path)
            for lit in ("AGENTS.md", ".agents", "CLAUDE.md", ".claude"):
                self.assertNotIn(lit, bodies, f"{lit} in {path}")
            self.assertIn("*.key", bodies, path)
        with open(os.path.join(out_dir, ".gitignore")) as f:
            gi = f.read()
        self.assertNotIn("**/AGENTS.md", gi)
        self.assertIn("*.key", gi)

    def test_bad_manifest_flag_warns_but_continues(self):
        write(self.target, ".startai-adopt.json",
              json.dumps({"files": {}, "layers": ["agents"],
                          "ai_files_visibility": "pubic"}))
        r = self._run(self.target, "--layers", "agents", "--infer-only")
        self.assertIn("ai_files_visibility", r.stderr)
        # treated as private -> report completes
        self.assertIn("Preflight findings", r.stdout)

    def test_target_config_json_tier_resolves_mode(self):
        # No --config: the target's own config.json drives the mode.
        write(self.target, "config.json",
              json.dumps({"ai_files_visibility": "public"}))
        out_dir = os.path.join(self.tmp.name, "emit")
        r = self._run(self.target, "--layers", "hooks,audit",
                      "--emit-dir", out_dir, "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(out_dir, "scripts/git/pre-commit")) as f:
            self.assertNotIn("'AGENTS.md'", f.read())

    def test_target_config_json_beats_manifest(self):
        # Precedence: target config.json > manifest.
        write(self.target, ".startai-adopt.json",
              json.dumps({"files": {}, "layers": ["agents"],
                          "ai_files_visibility": "public"}))
        write(self.target, "config.json",
              json.dumps({"ai_files_visibility": "private"}))
        out_dir = os.path.join(self.tmp.name, "emit")
        # all enforcement layers -> the public->private flip guard stays silent
        r = self._run(self.target, "--layers", "agents,hooks,audit",
                      "--emit-dir", out_dir, "--infer-only")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(out_dir, "scripts/git/pre-commit")) as f:
            self.assertIn("'AGENTS.md'", f.read())

    def test_target_config_json_invalid_is_fatal(self):
        write(self.target, "config.json",
              json.dumps({"ai_files_visibility": "pubic"}))
        r = self._run(self.target, "--layers", "agents", "--infer-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ai_files_visibility", r.stderr + r.stdout)

    def test_cli_config_without_key_falls_through_to_target(self):
        # --config lacking ai_files_visibility must NOT hard-pin "private":
        # resolution falls through to the target chain.
        write(self.target, "config.json",
              json.dumps({"ai_files_visibility": "public"}))
        nokey = helpers.load_module().load_defaults()
        nokey.pop("ai_files_visibility", None)
        cfg = os.path.join(self.tmp.name, "nokey.json")
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(nokey, f)
        out_dir = os.path.join(self.tmp.name, "emit")
        r = self._run(self.target, "--layers", "hooks,audit",
                      "--emit-dir", out_dir, "--config", cfg)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(out_dir, "scripts/git/pre-commit")) as f:
            self.assertNotIn("'AGENTS.md'", f.read())

    def test_non_dict_config_json_and_manifest_warn_not_crash(self):
        write(self.target, "config.json", '"just a string"\n')
        write(self.target, ".startai-adopt.json", "[1, 2, 3]\n")
        r = self._run(self.target, "--layers", "agents", "--infer-only")
        self.assertIn("manifest", r.stderr.lower())
        self.assertIn("Preflight findings", r.stdout)

    def test_wizard_flip_reruns_preflight(self):
        # Scripted wizard: accept defaults, answer "public" at the flag
        # prompt -> preflight must re-run under the new mode.
        mod = helpers.load_module()
        n_questions = len(mod.load_defaults())
        answers = "\n" * (n_questions - 1) + "public\n"
        r = self._run(self.target, "--apply", "--layers", "agents",
                      input_text=answers)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("re-running", r.stdout)
        with open(os.path.join(self.target, ".startai-adopt.json")) as f:
            self.assertEqual(json.load(f)["ai_files_visibility"], "public")
        with open(os.path.join(self.target, "AGENTS.md")) as f:
            self.assertIn("Contexto IA versionado", f.read())
        with open(os.path.join(self.target, ".gitignore")) as f:
            self.assertNotIn("**/AGENTS.md", f.read())


if __name__ == "__main__":
    unittest.main()
