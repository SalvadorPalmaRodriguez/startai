"""Integration tests: the scaffold() function produces a correct project tree."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest

import helpers

m = helpers.load_module()


class TestScaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "proj")
        self.config = m.load_defaults()

    def tearDown(self):
        self.tmp.cleanup()

    def scaffold(self):
        m.scaffold(self.target, self.config)

    def test_expected_files_present(self):
        self.scaffold()
        expected = [
            "README.md", "README.es.md", "AGENTS.md", "llms.txt", "llms-full.txt",
            "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md",
            "THIRD_PARTY_LICENSES.md", ".gitignore", ".devinignore",
            ".agents/README.md", ".agents/agents/developer.md", ".agents/agents/reviewer.md",
            ".agents/skills/ai-native/SKILL.md", ".agents/skills/distribution/SKILL.md",
            ".agents/skills/github-pages/SKILL.md", ".agents/skills/license/SKILL.md",
            ".agents/skills/signing/SKILL.md",
            "docs/_config.yml", "docs/index.md", "docs/README.md",
            "docs/_layouts/default.html", "docs/assets/hacker.css",
            "docs/en/index.md", "docs/en/ai-native.md", "docs/en/distribution.md",
            "docs/en/license.md", "docs/en/signing.md",
            "docs/es/index.md", "docs/es/ai-native.md", "docs/es/distribution.md",
            "docs/es/license.md", "docs/es/signing.md",
        ]
        for rel in expected:
            self.assertTrue(os.path.isfile(os.path.join(self.target, rel)), f"missing {rel}")

    def test_kit_index_is_not_scaffolded(self):
        # templates/README.md (the kit index) must not be copied; README.md is the EN project README.
        self.scaffold()
        with open(os.path.join(self.target, "README.md"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn(self.config["product_name"], content)
        self.assertIn("Features", content)

    def test_no_residual_tokens_except_liquid_layout(self):
        self.scaffold()
        liquid_layout = os.path.join("docs", "_layouts", "default.html")
        token_re = re.compile(r"\{\{\w+\}\}")
        for root, dirs, files in os.walk(self.target):
            for name in files:
                path = os.path.join(root, name)
                if not m.is_text(path):
                    continue
                rel = os.path.relpath(path, self.target)
                if rel == liquid_layout:
                    continue  # Liquid/Jekyll tags are expected and must stay
                with open(path, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.assertIsNone(token_re.search(content), f"unresolved token in {rel}")

    # TODO[token-walk]: Shared template token-walk | duplicates the walk in
    # self_check()/collect() (scripts/startai.py) — extract a shared helper if
    # it drifts again | pending | - | 2026-09-28 | low
    def test_all_template_tokens_are_defined(self):
        used = set()
        for root, dirs, files in os.walk(helpers.TEMPLATES_DIR):
            dirs[:] = [d for d in dirs if d not in m.SKIP_DIRS]
            rel = os.path.relpath(root, helpers.TEMPLATES_DIR)
            for name in files:
                if name.endswith(m.SKIP_SUFFIXES):
                    continue
                if rel == "." and name in m.EXCLUDE:
                    continue
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    used |= set(re.findall(r"\{\{(\w+)\}\}", f.read()))
        undefined = sorted(t for t in used if t not in self.config)
        self.assertEqual(undefined, [], f"tokens without config key: {undefined}")

    def test_license_is_substituted(self):
        self.scaffold()
        with open(os.path.join(self.target, "LICENSE"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn(self.config["product_name"], content)
        self.assertNotIn("{{", content)

    def test_readme_links_use_configured_repo(self):
        self.scaffold()
        with open(os.path.join(self.target, "README.md"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn(f"https://github.com/{self.config['github_user']}/{self.config['repo']}", content)

    def test_collect_has_no_residual_tokens(self):
        files = m.collect(self.config)
        self.assertTrue(files)
        liquid = os.path.join("docs", "_layouts", "default.html")
        token_re = re.compile(r"\{\{\w+\}\}")
        for rel, content in files.items():
            if rel == liquid:
                continue
            self.assertIsNone(token_re.search(content), rel)

    def test_scaffold_gitignore_is_private_context_version(self):
        self.scaffold()
        with open(os.path.join(self.target, ".gitignore"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn("**/AGENTS.md", content)
        self.assertIn(".agents/", content)

    def test_scaffold_scripts_are_present_and_executable(self):
        self.scaffold()
        for rel in ("scripts/check.py", "scripts/github.py",
                    "scripts/git/pre-commit", "scripts/git/pre-push",
                    "scripts/git/commit-msg", "scripts/git/install-hooks.sh"):
            path = os.path.join(self.target, rel)
            self.assertTrue(os.path.isfile(path), f"missing {rel}")
            self.assertTrue(os.access(path, os.X_OK), f"not executable: {rel}")

    def test_startai_root_gitignore_hides_ai_context(self):
        with open(os.path.join(helpers.REPO_ROOT, ".gitignore"), encoding="utf-8") as f:
            # active (non-comment, non-blank) lines only
            lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
        self.assertIn("**/AGENTS.md", lines)
        self.assertIn(".agents/", lines)
        self.assertIn(".devinignore", lines)

    def test_root_gitignore_keeps_templates_public(self):
        # Regression test for the unanchored-patterns bug: **/AGENTS.md, .agents/
        # and .devinignore must ignore the owner-private files at the repo root
        # but NOT the public copies under templates/. Checked with real git.
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            shutil.copy(os.path.join(helpers.REPO_ROOT, ".gitignore"),
                        os.path.join(tmp, ".gitignore"))
            public = [
                "templates/AGENTS.md",
                "templates/.agents/skills/ai-native/SKILL.md",
                "templates/.agents/agents/reviewer.md",
                "templates/.devinignore",
            ]
            private = ["AGENTS.md", ".agents/README.md", ".devinignore"]
            for rel in public + private:
                path = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, "w").close()
            subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
            listed = subprocess.run(
                ["git", "ls-files"], cwd=tmp, check=True,
                capture_output=True, text=True).stdout.split()
            for rel in public:
                self.assertIn(rel, listed)
            for rel in private:
                self.assertNotIn(rel, listed)

    def test_no_nested_gitignore_inside_templates(self):
        # A real templates/.gitignore would apply to paths under templates/ and
        # silently re-ignore the public templates even if the root .gitignore
        # negates them. The shipped gitignore template must stay non-magic
        # (templates/gitignore, renamed to .gitignore on generation).
        for root, dirs, files in os.walk(helpers.TEMPLATES_DIR):
            for name in files:
                self.assertNotEqual(name, ".gitignore",
                                    f"nested .gitignore at {os.path.join(root, name)}")

    def test_license_guide_documents_real_license_tokens(self):
        # The sed documented for manual LICENSE substitution must target exactly
        # the tokens that templates/LICENSE actually uses. Tokens may appear
        # literally ({{name}} or {{ name }}) or shell-built (${O}name${C}) so
        # that the docs survive render() and check.py.
        with open(os.path.join(helpers.TEMPLATES_DIR, "LICENSE"),
                  encoding="utf-8") as f:
            real = set(re.findall(r"\{\{([a-z_]+)\}\}", f.read()))
        docs = [
            os.path.join(helpers.REPO_ROOT, "docs", "en", "license.md"),
            os.path.join(helpers.REPO_ROOT, "docs", "es", "license.md"),
            os.path.join(helpers.TEMPLATES_DIR, ".agents", "skills",
                         "license", "SKILL.md"),
        ]
        for doc in docs:
            with open(doc, encoding="utf-8") as f:
                sed_lines = [ln for ln in f if ln.lstrip().startswith("sed ")]
            self.assertTrue(sed_lines, f"no sed documented in {doc}")
            documented = set()
            for ln in sed_lines:
                documented |= set(re.findall(r"\{\{\s*([a-z_]+)\s*\}\}", ln))
                documented |= set(re.findall(r"\$\{O\}([a-z_]+)\$\{C\}", ln))
            self.assertEqual(documented, real,
                             f"{doc}: documented tokens != LICENSE tokens")

    def test_agents_is_scaffolded_from_templates(self):
        self.scaffold()
        # .agents/README.md must NOT be excluded (only templates/README.md is the kit index)
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".agents", "README.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".agents", "skills", "ai-native", "SKILL.md")))


if __name__ == "__main__":
    unittest.main()
