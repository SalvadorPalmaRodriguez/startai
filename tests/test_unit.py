"""Unit tests for the pure functions of scripts/startai.py."""
import json
import os
import re
import tempfile
import unittest
from unittest import mock

import helpers

m = helpers.load_module()


class TestConfigLoading(unittest.TestCase):
    def test_defaults_have_all_required_keys(self):
        cfg = m.load_defaults()
        required = [
            "product_name", "product_slug", "owner", "email", "year",
            "github_user", "repo", "version", "platform", "language",
            "architecture", "tagline", "description", "purpose",
            "install_command", "command_tree", "dir_structure",
            "feature_1", "feature_2", "feature_3",
        ]
        for key in required:
            self.assertIn(key, cfg)

    def test_load_config_file_merges_missing_keys_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"product_name": "Foo", "email": "a@b.c"}, f)
            cfg = m.load_config_file(path)
        self.assertEqual(cfg["product_name"], "Foo")
        self.assertEqual(cfg["email"], "a@b.c")
        # missing keys fall back to defaults (read from config.example.json,
        # not hardcoded, so the test survives default changes)
        self.assertEqual(cfg["repo"], m.load_defaults()["repo"])


class TestRender(unittest.TestCase):
    def test_substitutes_known_tokens(self):
        self.assertEqual(m.render("Hello {{name}}!", {"name": "World"}), "Hello World!")

    def test_leaves_liquid_tags_untouched(self):
        text = "{{ page.url }} {{ site.title }} {{product_name}}"
        out = m.render(text, {"product_name": "Foo"})
        self.assertIn("{{ page.url }}", out)
        self.assertIn("{{ site.title }}", out)
        self.assertNotIn("{{product_name}}", out)

    def test_leaves_unknown_tokens_untouched(self):
        self.assertEqual(m.render("{{unknown}}", {"x": "y"}), "{{unknown}}")

    def test_empty_config_returns_text_unchanged(self):
        self.assertEqual(m.render("abc {{x}}", {}), "abc {{x}}")


class TestIsText(unittest.TestCase):
    def test_text_files(self):
        for name in ("a.md", "a.txt", "a.yml", "a.json", "a.html", "a.gitignore",
                     "a.devinignore", ".gitignore", ".devinignore"):
            self.assertTrue(m.is_text(name), name)

    def test_binary_files(self):
        for name in ("a.png", "a.jpg", "a.bin", "a.pdf", "a.gif"):
            self.assertFalse(m.is_text(name), name)


class TestPickEditor(unittest.TestCase):
    def test_env_editor_is_preferred(self):
        with mock.patch.dict(os.environ, {"EDITOR": "nano"}, clear=False):
            self.assertEqual(m.editor_command(), ["nano"])

    def test_gui_editor_gets_wait_flag(self):
        with mock.patch.dict(os.environ, {"EDITOR": "code"}, clear=False):
            self.assertEqual(m.editor_command(), ["code", "--wait"])

    def test_gui_editor_path_gets_wait_flag(self):
        with mock.patch.dict(os.environ, {"EDITOR": "/usr/bin/codium"}, clear=False):
            self.assertEqual(m.editor_command(), ["/usr/bin/codium", "--wait"])

    def test_none_when_no_editor_available(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(m.shutil, "which", return_value=None):
            self.assertIsNone(m.editor_command())


class TestReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "proj")
        os.makedirs(self.target)

    def tearDown(self):
        self.tmp.cleanup()

    def _one_file(self, content="old content"):
        path = os.path.join(self.target, "AGENTS.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_replace_with_existing_file(self):
        path = self._one_file()
        replacement = os.path.join(self.tmp.name, "my_agents.md")
        with open(replacement, "w", encoding="utf-8") as f:
            f.write("my own agents")
        responses = iter(["r", replacement])
        with mock.patch("builtins.input", side_effect=lambda _p: next(responses)), \
             mock.patch("builtins.print"):
            m.review(self.target)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "my own agents")

    def test_skip_removes_file(self):
        path = self._one_file()
        responses = iter(["s"])
        with mock.patch("builtins.input", side_effect=lambda _p: next(responses)), \
             mock.patch("builtins.print"):
            m.review(self.target)
        self.assertFalse(os.path.exists(path))

    def test_keep_all_keeps_remaining_files(self):
        p1 = self._one_file()
        p2 = os.path.join(self.target, "B.md")
        with open(p2, "w", encoding="utf-8") as f:
            f.write("b")
        responses = iter(["a"])
        with mock.patch("builtins.input", side_effect=lambda _p: next(responses)), \
             mock.patch("builtins.print"):
            m.review(self.target)
        self.assertTrue(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))

    def test_edit_invokes_editor(self):
        self._one_file()
        responses = iter(["e"])
        with mock.patch("builtins.input", side_effect=lambda _p: next(responses)), \
             mock.patch("builtins.print"), \
             mock.patch.object(m.subprocess, "call", return_value=0) as call, \
             mock.patch.object(m, "editor_command", return_value=["fakeeditor"]):
            m.review(self.target)
        call.assert_called_once_with(["fakeeditor", os.path.join(self.target, "AGENTS.md")])


class TestWizard(unittest.TestCase):
    def _run_wizard(self, inputs, defaults=None):
        defaults = defaults or {"plain": "p0", "tree": "t1\nt2"}
        it = iter(inputs)
        with mock.patch("builtins.input", side_effect=lambda _p="": next(it)), \
             mock.patch("builtins.print"):
            return m.wizard(defaults)

    def test_multiline_reads_until_blank_line(self):
        cfg = self._run_wizard(["v", "line1", "line2", ""])
        self.assertEqual(cfg["plain"], "v")
        self.assertEqual(cfg["tree"], "line1\nline2")

    def test_multiline_first_empty_line_keeps_default(self):
        cfg = self._run_wizard(["v", ""])
        self.assertEqual(cfg["tree"], "t1\nt2")

    def test_multiline_single_line_value(self):
        cfg = self._run_wizard(["v", "only one line", ""])
        self.assertEqual(cfg["tree"], "only one line")

    def test_single_line_empty_keeps_default(self):
        cfg = self._run_wizard(["", "x", ""])
        self.assertEqual(cfg["plain"], "p0")


class TestValidateConfig(unittest.TestCase):
    def test_example_config_is_valid(self):
        self.assertEqual(m.validate_config(m.load_defaults()), [])

    def test_example_json_has_no_empty_values(self):
        with open(helpers.CONFIG_EXAMPLE, encoding="utf-8") as f:
            data = json.load(f)
        for key, value in data.items():
            self.assertTrue(isinstance(value, str) and value.strip(),
                            f"empty value for: {key}")

    def test_detects_empty_string_value(self):
        cfg = m.load_defaults()
        cfg["email"] = "   "
        problems = m.validate_config(cfg)
        self.assertTrue(any("email" in p for p in problems))

    def test_detects_none_value(self):
        cfg = m.load_defaults()
        cfg["owner"] = None
        problems = m.validate_config(cfg)
        self.assertTrue(any("owner" in p for p in problems))

    def test_detects_missing_key(self):
        cfg = m.load_defaults()
        del cfg["repo"]
        problems = m.validate_config(cfg)
        self.assertTrue(any("repo" in p for p in problems))


class TestSelfCheck(unittest.TestCase):
    def test_self_check_passes(self):
        self.assertTrue(m.self_check())

    def test_self_check_detects_empty_value(self):
        cfg = m.load_defaults()
        cfg["email"] = ""
        with mock.patch.object(m, "load_defaults", return_value=cfg), \
             mock.patch("builtins.print"):
            self.assertFalse(m.self_check())

    def test_self_check_detects_undefined_token(self):
        cfg = m.load_defaults()
        del cfg["product_name"]
        with mock.patch.object(m, "load_defaults", return_value=cfg), \
             mock.patch("builtins.print"):
            self.assertFalse(m.self_check())


def _golden_private(text):
    """Independent reference stripper: private render = template minus
    sentinel lines and minus if-ai-public blocks (markers dropped)."""
    out, drop = [], False
    for line in text.split("\n"):
        mo = m.VIS_OPEN_RE.match(line)
        if mo:
            drop = mo.group(1) == "ai-public"
            continue
        if m.VIS_CLOSE_RE.match(line):
            drop = False
            continue
        if not drop:
            out.append(line)
    return "\n".join(out)


def _template_rels():
    """{out_rel: template_path} for every shipped template."""
    rels = {}
    for root, dirs, fs in os.walk(helpers.TEMPLATES_DIR):
        dirs[:] = [d for d in dirs if d not in m.SKIP_DIRS]
        rel = os.path.relpath(root, helpers.TEMPLATES_DIR)
        for name in fs:
            if name.endswith(m.SKIP_SUFFIXES):
                continue
            if rel == "." and name in m.EXCLUDE:
                continue
            out_name = m.RENAME.get(name, name)
            out_rel = out_name if rel == "." else os.path.join(rel, out_name)
            rels[out_rel] = os.path.join(root, name)
    return rels


class TestVisibilityMarkers(unittest.TestCase):
    def _cfg(self, mode=None):
        cfg = m.load_defaults()
        if mode is not None:
            cfg["ai_files_visibility"] = mode
        return cfg

    def test_default_mode_is_private(self):
        files = m.collect(self._cfg())
        self.assertIn("**/AGENTS.md", files[".gitignore"])

    def test_private_render_keeps_ai_context_blocked(self):
        files = m.collect(self._cfg("private"))
        gi = files[".gitignore"]
        for pat in ("**/AGENTS.md", ".agents/", "CLAUDE.md", ".claude/"):
            self.assertIn(pat, gi)
        hook = files["scripts/git/pre-commit"]
        conf = files["scripts/dev/audit/profiles/project.conf"]
        for lit in ("'AGENTS.md'", "'.agents/*'", "'CLAUDE.md'", "'.claude/*'",
                    "'**/AGENTS.md'", "'.agents/'", "'.claude/'"):
            self.assertIn(lit, hook)
            self.assertIn(lit, conf)

    def test_public_render_drops_ai_context_keeps_secrets(self):
        files = m.collect(self._cfg("public"))
        gi = files[".gitignore"]
        active = [l.strip() for l in gi.splitlines()
                  if l.strip() and not l.startswith("#")]
        for pat in ("**/AGENTS.md", ".agents/", "CLAUDE.md", ".claude/"):
            self.assertNotIn(pat, active)
        for pat in ("*.key", "*.pem", ".env", ".env*", ".devinignore",
                    "history_*.md", "NOTES.md", "config.json",
                    ".startai-adopt.json", "scripts/dev/", "docs/dev/",
                    "security-audit/", ".devin/"):
            self.assertIn(pat, active)
        hook = files["scripts/git/pre-commit"]
        conf = files["scripts/dev/audit/profiles/project.conf"]
        array_re = re.compile(r"(PRIVATE_GLOBS|REQUIRED_GITIGNORE)=\((.*?)\)",
                              re.S)
        for text in (hook, conf):
            bodies = "\n".join(b for _, b in array_re.findall(text))
            self.assertTrue(bodies.strip(), "arrays not found")
            for lit in ("'AGENTS.md'", "'.agents/*'", "'CLAUDE.md'",
                        "'.claude/*'", "'**/AGENTS.md'", "'.agents/'",
                        "'.claude/'"):
                self.assertNotIn(lit, bodies)
            for lit in ("'*.key'", "'*.pem'", "'.env'", "'history_*.md'",
                        "'config.json'", "'.devinignore'", "'scripts/dev/*'",
                        "'security-audit/*'", "'.devin/*'"):
                self.assertIn(lit, bodies)

    def test_no_marker_residue_in_either_mode(self):
        for mode in ("private", "public"):
            files = m.collect(self._cfg(mode))
            for rel, content in files.items():
                self.assertNotIn("startai:", content,
                                 f"marker residue in {rel} ({mode})")

    def test_invalid_visibility_is_fatal(self):
        for bad in ("pubic", "Public1", "both", "", "yes"):
            with self.assertRaises(SystemExit, msg=bad), \
                 mock.patch("sys.stderr"):
                m.collect(self._cfg(bad))

    def test_missing_key_defaults_to_private(self):
        cfg = self._cfg()
        del cfg["ai_files_visibility"]
        files = m.collect(cfg)
        self.assertIn("**/AGENTS.md", files[".gitignore"])

    def test_case_insensitive_value_normalized(self):
        files = m.collect(self._cfg("PUBLIC"))
        self.assertNotIn("**/AGENTS.md", files[".gitignore"])

    def test_marker_in_config_value_is_fatal(self):
        cfg = self._cfg()
        cfg["tagline"] = "x\n# >>> startai:if-ai-public >>>"
        with self.assertRaises(SystemExit), mock.patch("sys.stderr"):
            m.collect(cfg)

    def test_validate_config_flags_enum_and_marker_text(self):
        cfg = self._cfg("pubic")
        problems = m.validate_config(cfg)
        self.assertTrue(any("ai_files_visibility" in p for p in problems))
        cfg = self._cfg()
        cfg["tagline"] = "has startai: inside"
        problems = m.validate_config(cfg)
        self.assertTrue(any("marker" in p for p in problems))

    def test_apply_visibility_errors_are_fatal(self):
        cases = [
            "x\n# <<< startai:endif <<<\n",               # close without open
            "# >>> startai:if-ai-private >>>\ncontent\n",  # EOF in block
            ("# >>> startai:if-ai-private >>>\n"
             "# >>> startai:if-ai-public >>>\n"),          # nesting
            "# >>> startai:if-ai-privte >>>\nx\n",         # typo sentinel
            "texto con startai: inline\n",                 # non-sentinel line
        ]
        for text in cases:
            with self.assertRaises(SystemExit, msg=text[:40]), \
                 mock.patch("sys.stderr"):
                m._apply_visibility(text, "private", "f.md")

    def test_apply_visibility_modes(self):
        text = ("a\n"
                "# >>> startai:if-ai-private >>>\nP\n"
                "# <<< startai:endif <<<\n"
                "# >>> startai:if-ai-public >>>\nU\n"
                "# <<< startai:endif <<<\n"
                "z\n")
        self.assertEqual(m._apply_visibility(text, "private", "f"), "a\nP\nz\n")
        self.assertEqual(m._apply_visibility(text, "public", "f"), "a\nU\nz\n")

    def test_private_render_matches_template_minus_public_blocks(self):
        # Golden check: every shipped template renders in private mode
        # exactly as the template reads minus sentinels/if-ai-public blocks.
        cfg = self._cfg()
        files = m.collect(cfg)
        rels = _template_rels()
        for out_rel, src in rels.items():
            with open(src, encoding="utf-8") as f:
                expected = _golden_private(m.render(f.read(), cfg))
            self.assertEqual(files[out_rel], expected, out_rel)

    def test_rendered_agents_md_within_budget_both_modes(self):
        for mode in ("private", "public"):
            files = m.collect(self._cfg(mode))
            self.assertLessEqual(
                len(files["AGENTS.md"].splitlines()), 120, mode)

    def test_wizard_visibility_restricted(self):
        defaults = {"ai_files_visibility": "private"}
        it = iter(["pubic", "PUBLIC"])
        with mock.patch("builtins.input", side_effect=lambda _p="": next(it)), \
             mock.patch("builtins.print"):
            cfg = m.wizard(defaults)
        self.assertEqual(cfg["ai_files_visibility"], "public")


class TestCheckMarkers(unittest.TestCase):
    def test_valid_blocks_are_clean(self):
        text = ("# >>> startai:if-ai-private >>>\na\n"
                "# <<< startai:endif <<<\n"
                "<!-- >>> startai:if-ai-public >>>\nb\n"
                "<!-- <<< startai:endif <<<\n")
        self.assertEqual(m._check_markers(text, "ok.md"), [])

    def test_flags_malformed_and_unbalanced(self):
        cases = {
            "endif without opening": "# <<< startai:endif <<<\n",
            "unclosed at EOF": "# >>> startai:if-ai-private >>>\nx\n",
            "nested": ("# >>> startai:if-ai-private >>>\n"
                       "# >>> startai:if-ai-public >>>\n"
                       "# <<< startai:endif <<<\n"
                       "# <<< startai:endif <<<\n"),
            "typo sentinel": "# >>> startai:if-ai-privte >>>\nx\n",
            "inline startai:": "texto con startai: dentro\n",
            "uppercase": "# >>> STARTAI:IF-AI-PRIVATE >>>\nx\n",
        }
        for name, text in cases.items():
            self.assertTrue(m._check_markers(text, "f.md"), name)


class TestSelfCheckMarkerBans(unittest.TestCase):
    """self_check() must flag markers where they are banned."""

    def _tmp_templates(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for rel, content in files.items():
            path = os.path.join(tmp.name, rel)
            os.makedirs(os.path.dirname(path) or tmp.name, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content or "")
        return tmp.name

    def test_json_template_with_marker_is_flagged(self):
        tmpl = self._tmp_templates({
            "x.json": '{ "a": "# >>> startai:if-ai-private >>>" }\n'})
        with mock.patch.object(m, "TEMPLATES", tmpl), \
             mock.patch("builtins.print"):
            self.assertFalse(m.self_check())

    def test_docs_copy_file_with_marker_is_flagged(self):
        root = self._tmp_templates({
            "doc.md": "texto\n# >>> startai:if-ai-private >>>\nx\n"})
        with mock.patch.object(m, "ROOT", root), \
             mock.patch.object(m, "DOCS_COPY_PATHS", ["doc.md"]), \
             mock.patch("builtins.print"):
            self.assertFalse(m.self_check())

    def test_docs_copy_unreadable_file_is_flagged_not_crash(self):
        root = self._tmp_templates({"blob.md": None})
        with open(os.path.join(root, "blob.md"), "wb") as f:
            f.write(b"\xff\xfe\x00\x01")
        with mock.patch.object(m, "ROOT", root), \
             mock.patch.object(m, "DOCS_COPY_PATHS", ["blob.md"]), \
             mock.patch("builtins.print"):
            self.assertFalse(m.self_check())


if __name__ == "__main__":
    unittest.main()
