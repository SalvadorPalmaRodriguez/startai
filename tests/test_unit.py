"""Unit tests for the pure functions of scripts/startai.py."""
import json
import os
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


if __name__ == "__main__":
    unittest.main()
