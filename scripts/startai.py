#!/usr/bin/env python3
"""startai — scaffold a new AI-native, distribution-ready project from this kit.

Usage:
    # Interactive: asks every variable, then walks each generated file.
    python3 scripts/startai.py mi-proyecto

    # Non-interactive: read variables from a JSON config and render without asking.
    python3 scripts/startai.py mi-proyecto --config config.json

    # Preview everything without writing any file (dry run), and save it to a file.
    python3 scripts/startai.py mi-proyecto --config config.json --dry-run --dry-run-output preview.txt

    # Fail instead of only warning when the config has empty/missing values.
    python3 scripts/startai.py mi-proyecto --config config.json --strict

    # Interactive wizard, but skip the per-file review.
    python3 scripts/startai.py mi-proyecto --no-review

    # Adopt the kit inside an EXISTING project (layered, reversible):
    python3 scripts/startai.py adopt /path/to/project --report           # preflight only (default)
    python3 scripts/startai.py adopt /path/to/project --apply --layers agents
    python3 scripts/startai.py adopt --list-layers                       # show the layer table
    python3 scripts/startai.py adopt /path/to/project --manual           # manual checklist, writes nothing
    python3 scripts/startai.py adopt /path/to/project --emit-dir /tmp/staging  # render layers into DIR, target untouched

During the review, each generated file can be:
    [k] keep          [e] edit with your editor
    [r] replace with an existing file (you give the path)
    [s] skip/delete   [a] keep all remaining

Only the Python standard library is used — no external dependencies.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATES = os.path.join(ROOT, "templates")
CONFIG_EXAMPLE = os.path.join(ROOT, "config.example.json")

# Human-readable descriptions shown in the wizard.
HELP = {
    "product_name": "name of the software (display name)",
    "product_slug": "command/binary name (lowercase, no spaces)",
    "owner": "copyright holder (legal name)",
    "email": "contact for security reports and license matters",
    "year": "year(s) of publication",
    "github_user": "GitHub username (used in URLs)",
    "repo": "repository name (used in URLs)",
    "version": "initial version",
    "date": "documentation date (YYYY-MM-DD)",
    "platform": "target platform",
    "language": "primary language / stack",
    "architecture": "architecture description",
    "tagline": "short subtitle",
    "description": "one-line pitch",
    "purpose": "purpose sentence",
    "install_command": "install command (one line)",
    "command_tree": "command tree (multiline)",
    "dir_structure": "directory structure (multiline)",
    "feature_1": "README feature bullet 1",
    "feature_2": "README feature bullet 2",
    "feature_3": "README feature bullet 3",
    "ai_files_visibility": "AI context visibility — 'private' gitignores "
                           "AGENTS.md, .agents/, CLAUDE.md, .claude/; "
                           "'public' versions them",
}

# templates/ files that are NOT part of the scaffold (kit documentation).
EXCLUDE = {"README.md"}

# directories/files inside templates/ that must never be walked or shipped
# (interpreter caches, editor droppings — they are not template content and
# binary artifacts like *.pyc would break the UTF-8 reads below).
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_SUFFIXES = (".pyc", ".pyo")

# template filename -> scaffold filename (rename map).
# "gitignore" is shipped without a leading dot on purpose: a real
# templates/.gitignore would act as a nested gitignore inside the startai repo
# and re-ignore templates/AGENTS.md, templates/.agents/ and
# templates/.devinignore, defeating the negations in the root .gitignore.
RENAME = {"README.en.md": "README.md", "gitignore": ".gitignore"}

# docs/ paths copied verbatim (the identity pages come from templates/).
# Note: everything project-specific (README, AGENTS.md, LICENSE, SECURITY.md,
# CONTRIBUTING.md, CHANGELOG.md, THIRD_PARTY_LICENSES.md, .gitignore,
# .devinignore, .agents/, scripts/) now lives in templates/ — the root files
# are startai's own, not scaffold inputs.
# Generic assets are copied verbatim from the root; files with startai
# identity (social-preview.svg, docs/README.md) live in templates/ instead
# and are rendered with {{key}} placeholders like the rest of the scaffold.
DOCS_COPY_PATHS = [
    "docs/assets/logo.svg", "docs/assets/hacker.css",
    "docs/_layouts",
    "docs/en/ai-native.md", "docs/en/distribution.md",
    "docs/en/license.md", "docs/en/signing.md",
    "docs/es/ai-native.md", "docs/es/distribution.md",
    "docs/es/license.md", "docs/es/signing.md",
]

TEXT_SUFFIXES = (
    ".md", ".txt", ".yml", ".yaml", ".json", ".toml",
    ".html", ".css", ".svg", ".sh", ".py", ".gitignore", ".devinignore",
)

# ─── ai_files_visibility flag ────────────────────────────────────────────
# "private" (default): the AI-context class (AGENTS.md, .agents/, CLAUDE.md,
# .claude/) is gitignored and blocked by hooks/audit — the classic policy.
# "public": that class is versioned on purpose. Secrets and owner-private
# files stay blocked in EVERY mode.
AI_VIS_KEY = "ai_files_visibility"
AI_VIS_MODES = ("private", "public")

# Conditional-block sentinels processed by collect() after {{token}}
# substitution — whole lines, one per block edge, in the file's own comment
# syntax ("#" or "<!--"):
#   <comment> >>> startai:if-ai-private >>> ... <comment> <<< startai:endif <<<
#   <comment> >>> startai:if-ai-public  >>> ... <comment> <<< startai:endif <<<
# Any other line containing the marker prefix is a fatal template error
# (catches typos, inline use and unknown sentinels). In prose the blocks are
# referenced by name ("if-ai-private"/"if-ai-public"), never by the literal
# prefix — see templates/.agents/skills/ai-native/SKILL.md.
VIS_OPEN_RE = re.compile(
    r"^\s*(?:#|<!--)\s*>>>\s*startai:if-(ai-private|ai-public)\s*>>>\s*$")
VIS_CLOSE_RE = re.compile(
    r"^\s*(?:#|<!--)\s*<<<\s*startai:endif\s*<<<\s*$")
VIS_HINT = "startai:"  # forbidden substring outside valid sentinels

EDITOR_CANDIDATES = ("nano", "vim", "vi", "micro", "emacs", "code")

# GUI editors that return immediately unless asked to wait for the file to be
# closed (e.g. `code file` exits at once). Without a wait flag the review loop
# would move on while the user is still editing.
GUI_EDITOR_WAIT_FLAGS = {
    "code": "--wait",
    "code-insiders": "--wait",
    "codium": "--wait",
    "subl": "-w",
    "atom": "--wait",
    "gedit": "--wait",
    "zed": "--wait",
}


def load_defaults():
    with open(CONFIG_EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def load_config_file(path):
    """Load a user config file, falling back to defaults for missing keys."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    defaults = load_defaults()
    defaults.update(data)
    return defaults


def validate_config(config):
    """Return a list of problems: missing keys, empty values, an invalid
    ai_files_visibility enum, or forbidden marker text in values."""
    problems = []
    for key in load_defaults():
        if key not in config:
            problems.append(f"missing key: {key}")
            continue
        value = config[key]
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append(f"empty value for: {key}")
    vis = config.get(AI_VIS_KEY)
    if vis is not None and str(vis).strip().lower() not in AI_VIS_MODES:
        problems.append(f"invalid {AI_VIS_KEY}: {vis!r} "
                        f"(expected {', '.join(AI_VIS_MODES)})")
    # A config value must never carry sentinel text: a {{token}} expanding
    # to a marker line could silently drop rendered content.
    for key, value in config.items():
        if isinstance(value, str) and VIS_HINT in value.lower():
            problems.append(f"forbidden marker text in value of: {key}")
    return problems


def render(text, config):
    for key, value in config.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _vis_or_die(value, source):
    """Normalize the ai_files_visibility flag; fatal on invalid values.

    'private' and 'public' are the only accepted modes — a typo must never
    silently degrade to either policy.
    """
    v = "private" if value is None else str(value).strip().lower()
    if v not in AI_VIS_MODES:
        print(f"Error: invalid {AI_VIS_KEY}={value!r} (from {source}); "
              f"expected one of: {', '.join(AI_VIS_MODES)}.", file=sys.stderr)
        sys.exit(2)
    return v


def _vis_from_target(target, manifest):
    """Flag resolution without --config: target config.json > manifest >
    'private'. A bad config.json value is fatal; a bad manifest value only
    warns (it is treated as 'private')."""
    tcfg = os.path.join(target, "config.json")
    if os.path.isfile(tcfg):
        raw = None
        try:
            with open(tcfg, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: cannot parse {tcfg} ({exc}) — ignoring it for "
                  f"{AI_VIS_KEY} resolution.", file=sys.stderr)
        if isinstance(raw, dict) and raw.get(AI_VIS_KEY) is not None:
            return _vis_or_die(raw[AI_VIS_KEY], tcfg)
    mval = manifest.get(AI_VIS_KEY)
    if mval is not None:
        v = str(mval).strip().lower()
        if v in AI_VIS_MODES:
            return v
        print(f"WARNING: {ADOPT_MANIFEST} has invalid "
              f"{AI_VIS_KEY}={mval!r} — treating it as 'private'.",
              file=sys.stderr)
    return "private"


def _marker_fatal(rel, lineno, msg):
    print(f"Error: {rel}:{lineno}: {msg}", file=sys.stderr)
    sys.exit(2)


def _apply_visibility(text, mode, rel):
    """Emit `text` with visibility sentinel blocks resolved for `mode`.

    Sentinel lines are never emitted; content inside if-ai-private /
    if-ai-public blocks is kept only when the block name matches the mode.
    Malformed, nested, unpaired or unknown sentinels are fatal — a
    half-processed file must never reach the scaffold.
    """
    if VIS_HINT not in text.lower():
        return text
    out = []
    block = None  # None outside a block; else "ai-private" | "ai-public"
    for lineno, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        m_open = VIS_OPEN_RE.match(line)
        if m_open:
            if block is not None:
                _marker_fatal(rel, lineno,
                              f"nested sentinel inside '{block}' block")
            block = m_open.group(1)
            continue
        if VIS_CLOSE_RE.match(line):
            if block is None:
                _marker_fatal(rel, lineno, "endif sentinel without opening")
            block = None
            continue
        if VIS_HINT in line.lower():
            _marker_fatal(rel, lineno,
                          "malformed or unknown sentinel "
                          "(whole-line markers only)")
        if block is None or (block == "ai-private") == (mode == "private"):
            out.append(line)
    if block is not None:
        _marker_fatal(rel, "EOF", f"unclosed '{block}' sentinel block")
    return "\n".join(out)


def _check_markers(text, rel):
    """Validate sentinel-block grammar in one template file.

    Returns a list of problems (empty if clean): unbalanced, nested or
    unknown sentinels, and any other line containing the marker prefix.
    """
    problems = []
    block = None
    for lineno, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        m_open = VIS_OPEN_RE.match(line)
        if m_open:
            if block is not None:
                problems.append(f"{rel}:{lineno}: nested sentinel inside "
                                f"'{block}' block")
            else:
                block = m_open.group(1)
            continue
        if VIS_CLOSE_RE.match(line):
            if block is None:
                problems.append(f"{rel}:{lineno}: endif sentinel without "
                                "opening")
            else:
                block = None
            continue
        if VIS_HINT in line.lower():
            problems.append(f"{rel}:{lineno}: malformed or unknown sentinel")
    if block is not None:
        problems.append(f"{rel}: unclosed '{block}' sentinel block at EOF")
    return problems


def self_check():
    """Validate config.example.json and template/config token coherence.

    Returns True if everything is coherent, False otherwise. Used by --check
    and by the git hooks (scripts/git/pre-commit, pre-push).
    """
    problems = []
    config = load_defaults()
    problems += validate_config(config)

    used = set()
    for root, dirs, fs in os.walk(TEMPLATES):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, TEMPLATES)
        for name in fs:
            if name.endswith(SKIP_SUFFIXES):
                continue
            if rel == "." and name in EXCLUDE:
                continue
            used |= set(re.findall(r"\{\{(\w+)\}\}", _read(os.path.join(root, name))))

    for token in sorted(used):
        if token not in config:
            problems.append(f"undefined template token: {token}")

    # Visibility sentinels: grammar on every shipped template + outright
    # bans — no markers in *.json templates (no comment syntax) nor in
    # DOCS_COPY_PATHS files (copied verbatim).
    for root, dirs, fs in os.walk(TEMPLATES):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, TEMPLATES)
        for name in fs:
            if name.endswith(SKIP_SUFFIXES):
                continue
            if rel == "." and name in EXCLUDE:
                continue
            out_rel = name if rel == "." else os.path.join(rel, name)
            text = _read(os.path.join(root, name))
            problems += _check_markers(text, out_rel)
            if name.endswith(".json") and VIS_HINT in text.lower():
                problems.append(f"{out_rel}: JSON templates cannot use "
                                "visibility markers (no comment syntax)")
    for rel in DOCS_COPY_PATHS:
        src = os.path.join(ROOT, rel)
        paths = []
        if os.path.isdir(src):
            for root, dirs, fs in os.walk(src):
                paths += [os.path.join(root, f) for f in fs]
        elif os.path.isfile(src):
            paths.append(src)
        for path in paths:
            try:
                text = _read(path)
            except (OSError, UnicodeDecodeError) as exc:
                problems.append(f"{os.path.relpath(path, ROOT)}: cannot "
                                f"read file ({exc})")
                continue
            if VIS_HINT in text.lower():
                problems.append(f"{os.path.relpath(path, ROOT)}: "
                                "DOCS_COPY_PATHS files cannot use "
                                "visibility markers")

    if problems:
        for problem in problems:
            print("ERROR: " + problem, file=sys.stderr)
        return False
    print("OK: config.example.json and templates are coherent.")
    return True


def collect(config):
    """Render the whole scaffold in memory and return {rel_path: content}.

    Does NOT touch the filesystem (no writes). Used by both scaffold() and dry_run().
    """
    mode = _vis_or_die(config.get(AI_VIS_KEY, "private"), "configuration")
    for key, value in config.items():
        if isinstance(value, str) and VIS_HINT in value.lower():
            print(f"Error: forbidden marker text in config key '{key}'.",
                  file=sys.stderr)
            sys.exit(2)
    files = {}

    def add(rel, content):
        files[rel] = _apply_visibility(content, mode, rel)

    # 1. identity templates (templates/) with token substitution
    for root, dirs, fs in os.walk(TEMPLATES):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, TEMPLATES)
        for name in fs:
            if name.endswith(SKIP_SUFFIXES):
                continue
            if rel == "." and name in EXCLUDE:
                continue
            out_name = RENAME.get(name, name)
            out_rel = out_name if rel == "." else os.path.join(rel, out_name)
            add(out_rel, render(_read(os.path.join(root, name)), config))

    # 2. docs assets, layout and guide pages
    for rel in DOCS_COPY_PATHS:
        src = os.path.join(ROOT, rel)
        if os.path.isdir(src):
            for root, dirs, fs in os.walk(src):
                for fname in fs:
                    rel2 = os.path.relpath(os.path.join(root, fname), ROOT)
                    add(rel2, render(_read(os.path.join(root, fname)), config))
        else:
            add(rel, render(_read(src), config))

    return files


def write_scaffold(target, files):
    for rel, content in files.items():
        dst = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        # Keep scripts runnable: anything with a shebang becomes executable.
        if content.startswith("#!"):
            os.chmod(dst, 0o755)


def scaffold(target, config):
    write_scaffold(target, collect(config))


def dry_run(config, output_path=None):
    """Preview the resolved configuration and every rendered file; optionally save to a file."""
    files = collect(config)
    lines = ["DRY RUN — no files will be written.", "", "Configuration:"]
    for key, value in config.items():
        lines.append(f"  {key}: {value}")
    lines.append(f"\nFiles that would be created ({len(files) + 1}):")
    for rel in sorted(files):
        lines.append("  " + rel)
    lines.append("  config.json  (your resolved configuration)")
    lines.append("\n" + "=" * 70)
    lines.append("--- Rendered content preview ---")
    for rel in sorted(files):
        lines.append("\n" + "=" * 70)
        lines.append("FILE: " + rel)
        lines.append("=" * 70)
        lines.append(files[rel])
    preview = "\n".join(lines)
    print(preview)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(preview)
        print(f"\nPreview saved to: {output_path}", file=sys.stderr)
    return files


def _read_multiline(default):
    """Read a multiline value: lines until an empty line.

    An empty first line keeps the default untouched.
    """
    lines = []
    while True:
        line = input("  > ")
        if not line.strip():
            break
        lines.append(line.rstrip())
    return "\n".join(lines) if lines else default


def wizard(defaults):
    print("startai — project configuration")
    print("Press Enter to accept the default shown in [brackets].\n")
    config = {}
    for key, default in defaults.items():
        help_text = HELP.get(key, "")
        prompt = key + (" — " + help_text if help_text else "")
        if isinstance(default, str) and "\n" in default:
            print(f"{prompt} [multiline — empty line ends input; "
                  "Enter on the first line keeps the default]:")
            for line in default.split("\n"):
                print("    " + line)
            config[key] = _read_multiline(default)
        else:
            if key == AI_VIS_KEY:
                value = input(f"{prompt} ({'|'.join(AI_VIS_MODES)}) "
                              f"[{default}]: ").strip().lower()
                while value and value not in AI_VIS_MODES:
                    value = input(f"  invalid — enter "
                                  f"{' or '.join(AI_VIS_MODES)} "
                                  f"[{default}]: ").strip().lower()
                config[key] = value if value else default
            else:
                value = input(f"{prompt} [{default}]: ").strip()
                config[key] = value if value else default
    return config


def is_text(path):
    return path.endswith(TEXT_SUFFIXES)


def editor_command():
    """Return the editor invocation (list) or None.

    GUI editors get their "wait until the file is closed" flag appended so the
    review loop only continues after the user finishes editing.
    """
    raw = None
    for var in ("EDITOR", "VISUAL"):
        if os.environ.get(var):
            raw = os.environ[var]
            break
    if raw is None:
        for cand in EDITOR_CANDIDATES:
            if shutil.which(cand):
                raw = cand
                break
    if raw is None:
        return None
    cmd = raw.split()
    wait = GUI_EDITOR_WAIT_FLAGS.get(os.path.basename(cmd[0]))
    if wait:
        cmd.append(wait)
    return cmd


def review(target):
    print("\nNow reviewing the generated files.")
    print("[k] keep   [e] edit   [r] replace with existing file   [s] skip   [a] keep all remaining\n")
    editor = editor_command()
    keep_all = False
    for root, dirs, files in os.walk(target):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, target)
            # config.json is generated by us seconds ago — nothing to review
            if rel == "config.json" or not is_text(path):
                continue
            print("\n" + "=" * 70)
            print("FILE:", rel)
            print("=" * 70)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    print(f.read())
            except Exception as exc:
                print(f"(cannot read: {exc})")
            print("-" * 70)
            if keep_all:
                continue
            choice = input("[k/e/r/s/a]: ").strip().lower()
            if choice == "a":
                keep_all = True
            elif choice == "e":
                if not editor:
                    print("No editor found. Set $EDITOR, or use [r] to replace "
                          "this file with an existing one.")
                else:
                    subprocess.call(editor + [path])
            elif choice == "r":
                src = input("Path of the file to use instead: ").strip()
                src = os.path.expanduser(src)
                if not os.path.isfile(src):
                    print(f"Not a file: {src}")
                else:
                    shutil.copyfile(src, path)
                    print(f"replaced {rel} with {src}")
            elif choice == "s":
                os.remove(path)
                print(f"removed {rel}")


def run(target, config, do_review):
    if not target:
        target = config.get("product_slug") or "new-project"
    target = os.path.abspath(target)

    if os.path.exists(target) and os.listdir(target):
        print(f"Error: target directory not empty: {target}")
        sys.exit(1)

    os.makedirs(target, exist_ok=True)
    scaffold(target, config)

    # Persist the chosen configuration for reproducibility and reuse with --config.
    with open(os.path.join(target, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    if do_review:
        review(target)

    print("\nDone. Project scaffolded at:", target)
    print("Next steps:")
    print("  1. cd", target)
    print("  2. git init && git add -A && git commit")
    print("  3. review .gitignore / .devinignore and the generated LICENSE.")
    print("Re-run non-interactively later with (config.json is gitignored —")
    print("local generation state with your real owner/email, not published):")
    print(f"  python3 {os.path.join(ROOT, 'scripts', 'startai.py')} {target} --config {os.path.join(target, 'config.json')}")


# ─── adopt: bring the kit into an EXISTING project ───────────────────────
# run() above refuses non-empty targets; adopt is the layered, reversible
# path for projects that already exist. The real risk is not overwriting
# files but leaving the repo with every commit/push blocked by the generated
# hooks and audit profile, so the design is: preflight findings first, writes
# only under --apply, conflicts diverted to <path>.startai-new, and
# enforcement (git hooks) never installed automatically.

BLOCKER, WARN, INFO = "BLOCKER", "WARN", "INFO"

# Layer manifest: which scaffold paths belong to which adoptable capability.
# Pattern semantics: a trailing "/*" means "everything under this directory"
# (recursive prefix match — plain fnmatch 'X/*' would not reliably reach
# nested files like .agents/skills/x/SKILL.md across fnmatch versions);
# other patterns use fnmatch on the full repo-relative path. EVERY key of
# collect() must be claimed by some layer — tests/test_adopt.py enforces it,
# so adding a template without a layer assignment fails the suite.
LAYERS = {
    "agents": {
        "desc": "AI context: AGENTS.md, .agents/ (skills, roles, orchestrator), llms.txt/llms-full.txt",
        "patterns": ["AGENTS.md", ".agents/*", "llms.txt", "llms-full.txt"],
        "requires": [],
    },
    "hooks": {
        "desc": "git hooks + coherence check (scripts/git/, scripts/check.py)",
        "patterns": ["scripts/git/*", "scripts/check.py"],
        "requires": [],
    },
    "audit": {
        "desc": "audit framework and dev tooling (scripts/dev/)",
        "patterns": ["scripts/dev/*"],
        "requires": [],
    },
    "docs": {
        "desc": "bilingual EN/ES GitHub Pages site (docs/)",
        "patterns": ["docs/*"],
        "requires": [],
    },
    "distribution": {
        "desc": "README EN/ES, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, THIRD_PARTY_LICENSES, .github/",
        "patterns": ["README.md", "README.es.md", "LICENSE", "SECURITY.md",
                     "CONTRIBUTING.md", "CHANGELOG.md", "THIRD_PARTY_LICENSES.md", ".github/*"],
        "requires": [],
    },
    "release": {
        "desc": "signed update feed and publishing (feed/, scripts/github.py)",
        "patterns": ["feed/*", "scripts/github.py"],
        "requires": ["audit"],
    },
}

# collect() keys that are deliberately in no layer: local generation state.
# .gitignore/.devinignore get special additive treatment (managed block):
# .gitignore is applied on EVERY --apply (adopt always writes the manifest,
# so it must always stay ignored — and hooks/audit need the private split
# too), while .devinignore only makes sense with the agents layer (agent
# tooling access). config.json is scaffold-reproduction state adopt skips.
ADOPT_LOCAL_FILES = {".gitignore", ".devinignore", "config.json"}

# Same scan surface as templates/scripts/check.py: the adopt preflight must
# flag exactly the files that would make the generated hooks fail.
ADOPT_SKIP_DIRS = {".git", "__pycache__", "node_modules", "target", "venv", ".venv"}
# Same exclusion as SKIP_TOKEN_FILES in templates/scripts/check.py: files
# whose token-looking literals the generated check.py itself ignores (its
# own LEGACY_TOKEN_RE source, Jekyll layouts) must not trip this scan either
# — otherwise every hooks-layer re-adopt hits a phantom BLOCKER.
ADOPT_SKIP_TOKEN_FILES = {"docs/_layouts/default.html", "scripts/check.py"}
ADOPT_TOKEN_RE = re.compile(r"\{\{\w+\}\}")
ADOPT_LEGACY_TOKEN_RE = re.compile(r"\{[A-Z][A-Z_]{2,}\}|\{YYYY-MM-DD\}")

# Same policy as PRIVATE_GLOBS in templates/scripts/dev/audit/profiles/project.conf
# and templates/scripts/git/pre-commit (duplicated on purpose, like them:
# a clean clone of the adopted repo has neither the profile nor this kit).
# These are the ALWAYS-private globs — secrets and owner-private files that
# the ai_files_visibility flag never touches.
ADOPT_PRIVATE_GLOBS = [
    ".devin/*", ".devinignore", ".codeiumignore", ".windsurfignore",
    "NOTES.md", "MEGAPLAN-*.md", "history_*.md", "config.json",
    "docs/dev/*", "scripts/dev/*", "security-audit/*",
    "*.key", "*.pem", "*.p12", "*.pfx", ".env", ".env.*",
    "minisign.key", ".startai-adopt.json",
]

# AI-context globs governed by ai_files_visibility: they join the private
# set only in "private" mode; in "public" they are versioned on purpose.
ADOPT_AI_CONTEXT_GLOBS = ["AGENTS.md", ".agents/*", "CLAUDE.md", ".claude/*"]

# project.conf arrays whose entries are repo-relative paths ("path" or
# "path:kind"). On adopt, entries absent in the target are commented out
# (not deleted) so the user discovers and re-enables them.
ADOPT_CONF_PATH_ARRAYS = (
    "VERSION_TARGETS", "SECRET_SCAN_FILES", "SECRET_SCAN_DIRS",
    "MD_SCAN_FILES", "MD_SCAN_DIRS", "MARKER_SCAN_FILES", "MARKER_SCAN_DIRS",
)
ADOPT_CONF_NOTE = "# adopt: absent in this repo — uncomment when it exists"

# Idempotent markers for additive merges into .gitignore/.devinignore.
ADOPT_BLOCK_BEGIN = ("# >>> startai >>> managed block — regenerated by "
                     "`startai.py adopt`; do not edit by hand")
ADOPT_BLOCK_END = "# <<< startai <<<"

ADOPT_MANIFEST = ".startai-adopt.json"

# Files handled via the managed block (see ADOPT_LOCAL_FILES) instead of the
# regular layer patterns. .gitignore always joins the plan, .devinignore only
# with the agents layer.
ADOPT_MANAGED = (".gitignore", ".devinignore")


def _layer_match(pattern, rel):
    if pattern.endswith("/*"):
        return rel.startswith(pattern[:-1])  # "X/*" -> prefix "X/"
    return fnmatch.fnmatch(rel, pattern)


def layer_for(rel):
    """Return the name of the layer claiming rel, or None."""
    for name, layer in LAYERS.items():
        if any(_layer_match(p, rel) for p in layer["patterns"]):
            return name
    return None


def unassigned_paths(files):
    """collect() keys claimed by no layer (anti-drift check for tests)."""
    return sorted(r for r in files
                  if r not in ADOPT_LOCAL_FILES and layer_for(r) is None)


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(target, *args):
    """Run git -C target <args>; return stripped stdout or None on failure."""
    try:
        r = subprocess.run(["git", "-C", target, *args],
                           capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _is_git_repo(target):
    return _git(target, "rev-parse", "--is-inside-work-tree") == "true"


def _match_globs(path, globs):
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path, "*/" + g)
               for g in globs)


def doctor(target, layers, vis="private", manifest=None):
    """Preflight findings on an existing project.

    Returns a list of (severity, layer, message, remediation). Each check is
    evaluated only when the layer it protects is selected; layer None marks
    cross-cutting findings (git presence, dirty tree, visibility flips) that
    always apply. `vis` is the resolved ai_files_visibility mode and
    `manifest` the loaded .startai-adopt.json (used for flip detection).
    """
    findings = []

    def add(sev, layer, msg, fix):
        findings.append((sev, layer, msg, fix))

    is_git = _is_git_repo(target)
    if not is_git:
        add(WARN, None, "target is not a git repository",
            "file adoption still works; hooks/private-path checks degrade. "
            "Run 'git init' first if you want them.")

    # 9. layer dependencies
    for name in layers:
        for req in LAYERS[name]["requires"]:
            if req not in layers:
                add(BLOCKER, name, f"layer '{name}' requires layer '{req}'",
                    f"select both, e.g. --layers {req},{name}")

    # 1. template tokens that would collide with scripts/check.py
    if "hooks" in layers:
        culprits = []
        for root, dirs, fs in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ADOPT_SKIP_DIRS]
            for name in fs:
                if not name.endswith(TEXT_SUFFIXES):
                    continue
                path = os.path.join(root, name)
                rel = os.path.relpath(path, target)
                if rel in ADOPT_SKIP_TOKEN_FILES:
                    continue
                try:
                    content = _read(path)
                except (OSError, UnicodeDecodeError):
                    continue
                if ADOPT_TOKEN_RE.search(content) or ADOPT_LEGACY_TOKEN_RE.search(content):
                    culprits.append(rel)
        if culprits:
            shown = ", ".join(sorted(culprits)[:10])
            if len(culprits) > 10:
                shown += f" (+{len(culprits) - 10} more)"
            add(BLOCKER, "hooks",
                f"files contain {{token}}-style placeholders check.py would reject: {shown}",
                "exclude/rename them, add them to SKIP_TOKEN_FILES in scripts/check.py, "
                "or skip the hooks layer")

    # 2. private paths already tracked by git (only meaningful with hooks/audit)
    if is_git and ("hooks" in layers or "audit" in layers):
        tracked = (_git(target, "ls-files") or "").splitlines()
        hits = sorted(p for p in tracked
                      if _match_globs(p, ADOPT_PRIVATE_GLOBS))
        layer = "hooks" if "hooks" in layers else "audit"
        if hits:
            add(BLOCKER, layer,
                "private paths already tracked by git: " + ", ".join(hits[:10]),
                "git rm --cached them (they must never be published) or the "
                "pre-commit step 3 / audit check 23 will block")
        if vis == "private":
            ai_hits = sorted(p for p in tracked
                             if _match_globs(p, ADOPT_AI_CONTEXT_GLOBS))
            if ai_hits:
                add(BLOCKER, layer,
                    "AI-context paths tracked by git while "
                    f"{AI_VIS_KEY}=private: " + ", ".join(ai_hits[:10]),
                    "git rm --cached them — visibility is not retroactive: "
                    "git history keeps whatever was committed (un-publishing "
                    "needs an explicit history rewrite)")

    # 2b. visibility flip without its enforcement layers
    prev = (manifest or {}).get(AI_VIS_KEY)
    if prev is not None:
        prev_v = str(prev).strip().lower()
        if prev_v in AI_VIS_MODES and prev_v != vis:
            missing = [x for x in ("agents", "hooks", "audit")
                       if x not in layers]
            if missing:
                sev = BLOCKER if vis == "private" else WARN
                add(sev, None,
                    f"{AI_VIS_KEY} flips {prev_v} → {vis} but enforcement "
                    f"layers are not selected: {', '.join(missing)}",
                    "re-run with agents,hooks,audit so .gitignore, hooks and "
                    "the audit profile re-render in the new mode; already-"
                    "tracked AI files also need 'git rm --cached' "
                    "(visibility is not retroactive — history is not purged)")

    # 3. pre-existing git hooks / custom hooksPath
    if "hooks" in layers and is_git:
        hooks_dir = os.path.join(target, ".git", "hooks")
        for hook in ("pre-commit", "pre-push", "commit-msg"):
            path = os.path.join(hooks_dir, hook)
            if os.path.islink(path):
                if "scripts/git/" not in os.readlink(path):
                    add(BLOCKER, "hooks",
                        f".git/hooks/{hook} is a symlink to {os.readlink(path)}",
                        "install-hooks.sh would replace it; move it aside first")
            elif os.path.exists(path):
                add(BLOCKER, "hooks",
                    f".git/hooks/{hook} already exists",
                    "install-hooks.sh would overwrite it; merge it into "
                    "scripts/git/ or move it aside first")
        hooks_path = _git(target, "config", "core.hooksPath")
        if hooks_path:
            add(WARN, "hooks",
                f"core.hooksPath={hooks_path} — .git/hooks is ignored by git",
                "install-hooks.sh would be silently useless; install the "
                "hooks under that path instead")

    # 4. conflicting documentation generators
    if "docs" in layers:
        gens = ["mkdocs.yml", "docusaurus.config.js", "docusaurus.config.ts",
                "docs/conf.py", "docs/_config.yml"]
        hits = [g for g in gens if os.path.exists(os.path.join(target, g))]
        pkg = os.path.join(target, "package.json")
        if os.path.isfile(pkg):
            try:
                pkg_txt = _read(pkg)
            except OSError:
                pkg_txt = ""
            if re.search(r"docusaurus|vitepress|vuepress", pkg_txt, re.I):
                hits.append("package.json (docs generator dependency)")
        if hits:
            add(BLOCKER, "docs",
                "existing docs generator detected: " + ", ".join(hits),
                "the kit ships a bilingual Jekyll site under docs/; keep yours "
                "and deselect the docs layer")

    # 5. bilingual docs parity (check.py fails on asymmetric docs/en-docs/es)
    if "hooks" in layers:
        en_dir = os.path.join(target, "docs", "en")
        es_dir = os.path.join(target, "docs", "es")
        has_en, has_es = os.path.isdir(en_dir), os.path.isdir(es_dir)
        if has_en != has_es:
            add(WARN, "hooks", "docs/en exists but docs/es does not (or vice versa)",
                "check.py parity is only checked when both dirs exist, but the "
                "docs layer assumes bilingual structure")
        elif has_en and has_es:
            en = {f for f in os.listdir(en_dir) if f.endswith(".md")}
            es = {f for f in os.listdir(es_dir) if f.endswith(".md")}
            if en != es:
                add(WARN, "hooks",
                    "asymmetric docs/en vs docs/es .md sets: "
                    + ", ".join(sorted(en ^ es)),
                    "check.py fails on missing counterparts; add translations "
                    "or keep the sets equal")

    # 6. audit prerequisites
    if "audit" in layers or "release" in layers:
        chlog = os.path.join(target, "CHANGELOG.md")
        chlog_txt = _read(chlog) if os.path.isfile(chlog) else ""
        if not re.search(r"^## \[\d+\.\d+\.\d+\]", chlog_txt, re.M):
            add(WARN, "audit", "no CHANGELOG.md with a '## [x.y.z]' entry",
                "audit checks 19/21 read the version from CHANGELOG.md; "
                "create one or comment those checks in the profile")
        if not os.path.isfile(os.path.join(target, "README.es.md")):
            add(WARN, "audit", "no README.es.md",
                "the audit profile expects a bilingual README (version badge)")
        if not os.path.isfile(os.path.join(target, "llms-full.txt")):
            add(WARN, "audit", "no llms-full.txt",
                "VERSION_TARGETS expects a current_version marker there")
        agents_md = os.path.join(target, "AGENTS.md")
        if os.path.isfile(agents_md):
            n = sum(1 for _ in open(agents_md, encoding="utf-8", errors="replace"))
            if n > 120:
                add(WARN, "audit", f"AGENTS.md has {n} lines (audit max is 120)",
                    "trim it or raise AGENTS_MD_MAX in the audit profile")
        docs_dir = os.path.join(target, "docs")
        headerless = []
        if os.path.isdir(docs_dir):
            for root, dirs, fs in os.walk(docs_dir):
                dirs[:] = [d for d in dirs if d not in ADOPT_SKIP_DIRS]
                for name in fs:
                    if not name.endswith(".md"):
                        continue
                    rel = os.path.relpath(os.path.join(root, name), target)
                    try:
                        head = "\n".join(
                            open(os.path.join(root, name),
                                 encoding="utf-8", errors="replace")
                            .read().splitlines()[:15])
                    except OSError:
                        continue
                    if not re.search(r"\*\*(Version|Versión):\*\*", head) or \
                            not re.search(r"\*\*(Updated|Actualizado):\*\*", head):
                        headerless.append(rel)
        if headerless:
            add(WARN, "audit",
                "docs/*.md without Version/Updated header: "
                + ", ".join(sorted(headerless)[:10]),
                "audit check 05 expects doc headers; add them or exclude the files")

    # 8. dirty worktree: adopt output must be cleanly revertable
    if is_git and _git(target, "status", "--porcelain"):
        add(WARN, None, "working tree has uncommitted changes",
            "commit or stash first so 'adopt --apply' output can be reverted cleanly")

    return findings


def _adopt_conf_patch(content, target):
    """Comment out project.conf path entries absent in the target repo."""
    out = []
    active = False
    for line in content.splitlines(keepends=True):
        head = re.match(r"\s*([A-Z_]+)=\(", line)
        if head:
            active = head.group(1) in ADOPT_CONF_PATH_ARRAYS
        if active:
            if line.strip() == ")":
                active = False
            else:
                m = re.match(r'(\s*)"([^"]+)"(.*)$', line)
                if m:
                    path = m.group(2).split(":")[0]
                    if not os.path.exists(os.path.join(target, path)):
                        line = f'{m.group(1)}# "{m.group(2)}" {ADOPT_CONF_NOTE}\n'
        out.append(line)
    return "".join(out)


def _merge_managed_block(existing, rendered):
    """Insert or replace the marked startai block; never touch other lines."""
    block = ADOPT_BLOCK_BEGIN + "\n" + rendered.rstrip("\n") + "\n" + ADOPT_BLOCK_END + "\n"
    if existing is None:
        return block
    if ADOPT_BLOCK_END not in existing:
        # No complete block present — append instead of risking swallowing
        # user lines after a stray BEGIN marker.
        return existing.rstrip("\n") + "\n" + block
    out = []
    inside = False
    emitted = False
    for line in existing.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        if stripped == ADOPT_BLOCK_BEGIN:
            if not inside and not emitted:
                out.append(block)
                emitted = True
            inside = True
            continue
        if inside:
            if stripped == ADOPT_BLOCK_END:
                inside = False
            continue
        out.append(line)
    if not inside and not emitted:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append(block)
    return "".join(out)


def _load_manifest(target):
    path = os.path.join(target, ADOPT_MANIFEST)
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        print(f"WARNING: {path} is unreadable or not a JSON object — "
              "starting with an empty manifest.", file=sys.stderr)
    return {"files": {}, "layers": []}


def _kit_version():
    """First '## [x.y.z]' of this kit's CHANGELOG.md (the adopt version stamp)."""
    try:
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", _read(os.path.join(ROOT, "CHANGELOG.md")), re.M)
    except OSError:
        m = None
    return m.group(1) if m else "unknown"


def adopt_plan(target, config, layers, manifest):
    """Compute (rel, action, content) for every file of the selected layers.

    Actions: created | current | updated | conflict. 'updated' means the
    target file still matches the hash recorded by a previous adopt run, so
    it is kit-owned and safe to refresh in place.
    """
    files = collect(config)
    plan = []
    for rel in sorted(files):
        if layer_for(rel) not in layers:
            continue
        content = files[rel]
        if rel == "scripts/dev/audit/profiles/project.conf" and "audit" in layers:
            content = _adopt_conf_patch(content, target)
        dst = os.path.join(target, rel)
        if not os.path.exists(dst):
            plan.append((rel, "created", content))
            continue
        try:
            cur = _read(dst)
        except (OSError, UnicodeDecodeError):
            cur = None
        if cur == content:
            plan.append((rel, "current", content))
        elif manifest.get("files", {}).get(rel, {}).get("sha256") == _sha256(cur or ""):
            plan.append((rel, "updated", content))
        else:
            plan.append((rel, "conflict", content))

    # Managed-block files, special treatment (never claimed by LAYERS):
    # .gitignore is merged on every adopt run — the manifest must stay
    # ignored and hooks/audit need the private split; .devinignore only
    # joins the agents layer. The planned action mirrors what apply will do
    # so --report never understates the write.
    for rel in ADOPT_MANAGED:
        if rel == ".devinignore" and "agents" not in layers:
            continue
        dst = os.path.join(target, rel)
        existing = _read(dst) if os.path.isfile(dst) else None
        merged = _merge_managed_block(existing, files[rel])
        if existing is None:
            plan.append((rel, "created", merged))
        elif existing == merged:
            plan.append((rel, "current", merged))
        else:
            plan.append((rel, "merged", merged))
    return plan


def _write_file(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    if content.startswith("#!"):
        os.chmod(path, 0o755)


def adopt_apply(target, plan, layers, manifest, overwrite, vis="private"):
    """Write the plan; returns {rel: action_taken}. Diverts conflicts to
    <path>.startai-new unless overwrite is set. Managed-block entries carry
    no sha256: the file is a merge, the user's lines are outside our block."""
    actions = {}
    for rel, action, content in plan:
        dst = os.path.join(target, rel)
        managed = rel in ADOPT_MANAGED
        if action == "current":
            actions[rel] = ({"action": "current"} if managed else
                            {"sha256": _sha256(content), "action": "current"})
            continue
        if action == "conflict" and not overwrite:
            _write_file(dst + ".startai-new", content)
            # no sha256 on purpose: the user-owned file must keep conflicting
            actions[rel] = {"action": "conflict", "side": rel + ".startai-new"}
            continue
        _write_file(dst, content)
        taken = "overwritten" if action == "conflict" else action
        actions[rel] = ({"action": taken} if managed else
                        {"sha256": _sha256(content), "action": taken})

    manifest.setdefault("files", {}).update(actions)
    manifest["layers"] = sorted(set(manifest.get("layers", [])) | set(layers))
    manifest[AI_VIS_KEY] = vis
    manifest["kit_version"] = _kit_version()
    manifest["adopted_at"] = _date.today().isoformat()
    _write_file(os.path.join(target, ADOPT_MANIFEST),
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return actions


def infer_config(target):
    """Best-effort config defaults inferred from the existing project."""
    cfg = load_defaults()
    base = os.path.basename(os.path.abspath(target).rstrip(os.sep))
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", base.lower())).strip("-")
    cfg["product_slug"] = slug or base
    cfg["product_name"] = base

    remote = _git(target, "remote", "get-url", "origin")
    if remote:
        m = re.match(r"^(?:[^@]+@)?[^:/]+[:/](.+?)(?:\.git)?$", remote)
        if m:
            parts = m.group(1).strip("/").split("/")
            if len(parts) >= 2:
                cfg["github_user"], cfg["repo"] = parts[-2], parts[-1]
            elif parts:
                cfg["repo"] = parts[-1]

    # Manifest files: product name, fallback version, language.
    pkg = os.path.join(target, "package.json")
    if os.path.isfile(pkg):
        try:
            data = json.load(open(pkg, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if data.get("name"):
            cfg["product_name"] = data["name"]
            cfg["product_slug"] = re.sub(r"[^a-z0-9-]+", "-", data["name"].lower())
        if data.get("version"):
            cfg["version"] = str(data["version"])
        cfg["language"] = "JavaScript"
    for fname, lang in (("pyproject.toml", "Python"), ("Cargo.toml", "Rust")):
        path = os.path.join(target, fname)
        if os.path.isfile(path):
            txt = _read(path)
            m = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
            if m:
                cfg["product_name"] = m.group(1)
            m = re.search(r'^version\s*=\s*"([^"]+)"', txt, re.M)
            if m:
                cfg["version"] = m.group(1)
            cfg["language"] = lang
    if os.path.isfile(os.path.join(target, "go.mod")):
        cfg["language"] = "Go"

    # CHANGELOG wins over manifest versions (canonical source in this kit).
    chlog = os.path.join(target, "CHANGELOG.md")
    if os.path.isfile(chlog):
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", _read(chlog), re.M)
        if m:
            cfg["version"] = m.group(1)

    owner = _git(target, "config", "user.name")
    email = _git(target, "config", "user.email")
    if owner:
        cfg["owner"] = owner
    if email:
        cfg["email"] = email
    today = _date.today()
    cfg["year"], cfg["date"] = str(today.year), today.isoformat()

    # Selective merge: the only key taken from an existing config.json is
    # the visibility flag (owner/email/date are re-inferred fresh).
    tcfg = os.path.join(target, "config.json")
    if os.path.isfile(tcfg):
        try:
            with open(tcfg, encoding="utf-8") as f:
                prev_cfg = json.load(f)
        except (OSError, json.JSONDecodeError):
            prev_cfg = {}
        if isinstance(prev_cfg, dict) and \
                prev_cfg.get(AI_VIS_KEY) is not None:
            cfg[AI_VIS_KEY] = prev_cfg[AI_VIS_KEY]
    return cfg


def print_findings(findings):
    """Grouped report; returns (n_blockers, n_warnings, n_info)."""
    order = {BLOCKER: 0, WARN: 1, INFO: 2}
    counts = {BLOCKER: 0, WARN: 0, INFO: 0}
    by_layer = {}
    for sev, layer, msg, fix in findings:
        counts[sev] += 1
        by_layer.setdefault(layer or "general", []).append((sev, msg, fix))
    print("\nPreflight findings:")
    if not findings:
        print("  none — clean target")
    for layer in sorted(by_layer):
        print(f"\n  [{layer}]")
        for sev, msg, fix in sorted(by_layer[layer], key=lambda x: order[x[0]]):
            print(f"    {sev}: {msg}")
            print(f"      → {fix}")
    print(f"\nSummary: {counts[BLOCKER]} blocker(s), "
          f"{counts[WARN]} warning(s), {counts[INFO]} info")
    return counts[BLOCKER], counts[WARN], counts[INFO]


def adopt_emit(emit_dir, target, config, layers):
    """Render the selected layers into emit_dir (the target is never touched).

    Staging for the manual workflow and for diffing against the real repo.
    The managed-block files are emitted as standalone blocks (markers
    included), so `cat staging/.gitignore >> target/.gitignore` reproduces
    exactly what --apply would merge.
    """
    files = collect(config)
    written = []
    for rel in sorted(files):
        if layer_for(rel) not in layers:
            continue
        content = files[rel]
        if rel == "scripts/dev/audit/profiles/project.conf" and "audit" in layers:
            content = _adopt_conf_patch(content, target)
        _write_file(os.path.join(emit_dir, rel), content)
        written.append(rel)
    for rel in ADOPT_MANAGED:
        if rel == ".devinignore" and "agents" not in layers:
            continue
        _write_file(os.path.join(emit_dir, rel),
                    _merge_managed_block(None, files[rel]))
        written.append(rel)
    return written


def print_manual(target, layers, files):
    """Print a correct two-phase manual-adoption checklist.

    Manual never means `cp` from templates/ — those carry {{tokens}} that
    check.py would reject; kit files must be rendered first (--emit-dir) and
    copied from the staging dir. Derived from the same LAYERS dict so it
    cannot drift out of sync with templates/.
    """
    script = os.path.abspath(__file__)
    staging = "/tmp/startai-staging"
    layer_arg = ",".join(layers)
    print("Manual adoption checklist (writes nothing — copy/paste friendly).\n")
    print("# 1. Preflight (no writes):")
    print(f"python3 {script} adopt {target} --layers {layer_arg} --report")
    print("\n# 2. Render the selected layers into a staging dir:")
    print(f"python3 {script} adopt {target} --layers {layer_arg} "
          f"--emit-dir {staging} --infer-only")
    print("\n# 3. Copy each RENDERED file into the project:")
    for name in layers:
        layer = LAYERS[name]
        print(f"# ── layer: {name} — {layer['desc']}")
        for rel in sorted(files):
            if layer_for(rel) == name:
                dst = os.path.dirname(rel)
                if dst:
                    print(f"mkdir -p {os.path.join(target, dst)}")
                print(f"cp {os.path.join(staging, rel)} "
                      f"{os.path.join(target, rel)}")
        print()
    print("# 4. Private split — append the managed block (the staging copies")
    print("#    already carry the >>> startai >>> markers):")
    print(f"cat {os.path.join(staging, '.gitignore')} "
          f">> {os.path.join(target, '.gitignore')}")
    if "agents" in layers:
        print(f"cat {os.path.join(staging, '.devinignore')} "
              f">> {os.path.join(target, '.devinignore')}")
    if "hooks" in layers:
        print("\n# 5. Hooks are opt-in: review first, then")
        print(f"bash {os.path.join(target, 'scripts/git/install-hooks.sh')}")
    print("\n# Manual adoption is supported, but without the manifest "
          f"({ADOPT_MANIFEST}) re-runs cannot detect kit-owned vs "
          "user-edited files.")
    print("# The step-4 append is not idempotent like --apply is: on a repeat "
          f"manual adoption, delete the existing '{ADOPT_BLOCK_END}' block first.")


def main_adopt(argv):
    p = argparse.ArgumentParser(prog="startai.py adopt",
                                description="Adopt the startai kit into an existing project.")
    p.add_argument("target", nargs="?", default=".",
                   help="existing project directory (default: current directory)")
    p.add_argument("--layers", default="agents",
                   help="comma-separated layer list (default: agents)")
    p.add_argument("--all-layers", action="store_true", help="select every layer")
    p.add_argument("--list-layers", action="store_true", help="print the layer table and exit")
    p.add_argument("--report", action="store_true",
                   help="preflight only, write nothing (default behaviour)")
    p.add_argument("--apply", action="store_true", help="actually write files")
    p.add_argument("--emit-dir", metavar="DIR",
                   help="render the selected layers into DIR without touching "
                        "the target — staging for --manual or for diffing")
    p.add_argument("--config", metavar="FILE", help="explicit JSON config (skips inference/wizard)")
    p.add_argument("--infer-only", action="store_true",
                   help="use inferred values + defaults without asking")
    p.add_argument("--overwrite", action="store_true",
                   help="overwrite conflicting files instead of writing .startai-new")
    p.add_argument("--force", action="store_true", help="proceed despite BLOCKER findings")
    p.add_argument("--manual", action="store_true",
                   help="print a manual-adoption checklist and exit")
    p.add_argument("--strict", action="store_true",
                   help="treat WARNINGs as blocking (exit 1 even if writes completed)")
    a = p.parse_args(argv)

    if a.list_layers:
        print("Adoption layers:")
        for name, layer in LAYERS.items():
            req = f" (requires: {', '.join(layer['requires'])})" if layer["requires"] else ""
            print(f"  {name:13} {layer['desc']}{req}")
        return 0

    layers = list(LAYERS) if a.all_layers else [
        x.strip() for x in a.layers.split(",") if x.strip()]
    unknown = [x for x in layers if x not in LAYERS]
    if unknown:
        print(f"Error: unknown layer(s): {', '.join(unknown)} "
              f"(valid: {', '.join(LAYERS)})", file=sys.stderr)
        return 2
    if not layers:
        print(f"Error: no layers selected (--layers is empty; "
              f"valid: {', '.join(LAYERS)})", file=sys.stderr)
        return 2

    target = os.path.abspath(a.target)
    if not os.path.isdir(target):
        print(f"Error: not a directory: {target}", file=sys.stderr)
        return 2

    manifest = _load_manifest(target)

    # The visibility flag resolves BEFORE any private-path check:
    # --config > target config.json > .startai-adopt.json > "private".
    if a.config:
        # --config wins ONLY when it actually defines the key: read the raw
        # JSON (load_config_file merges defaults, which would mask the key's
        # absence as an explicit "private" — a phantom flip).
        try:
            with open(a.config, encoding="utf-8") as f:
                raw_cfg = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Error: cannot parse --config {a.config}: {exc}",
                  file=sys.stderr)
            return 2
        if not isinstance(raw_cfg, dict):
            print(f"Error: --config {a.config} is not a JSON object",
                  file=sys.stderr)
            return 2
        if raw_cfg.get(AI_VIS_KEY) is not None:
            vis = _vis_or_die(raw_cfg[AI_VIS_KEY], f"--config {a.config}")
        else:
            vis = _vis_from_target(target, manifest)
    else:
        vis = _vis_from_target(target, manifest)

    if a.manual:
        cfg = load_config_file(a.config) if a.config else infer_config(target)
        cfg[AI_VIS_KEY] = vis
        print_manual(target, layers, collect(cfg))
        return 0

    # Preflight first: doctor() needs no full config, and a bare report must
    # not block on the ~21-question wizard.
    findings = doctor(target, layers, vis, manifest)
    n_blockers, n_warns, _ = print_findings(findings)

    # The wizard only runs when files will actually be rendered
    # (--apply/--emit-dir); report mode uses inferred values silently.
    inferred = infer_config(target)
    inferred[AI_VIS_KEY] = vis  # wizard default = resolved mode
    if a.config:
        config = load_config_file(a.config)
    elif a.infer_only:
        config = inferred
    elif a.apply or a.emit_dir:
        config = wizard(inferred)
    else:
        config = inferred
        print("\n(values below come from inference; the wizard runs on --apply)")

    # The flag is fatal, not --strict-dependent. With --config it was
    # already resolved above (a merged default must not re-impose
    # "private" over the target chain); without it, the wizard's answer
    # or the inferred value is authoritative — re-run preflight when the
    # wizard flips the mode.
    if a.config:
        config[AI_VIS_KEY] = vis
    else:
        vis_final = _vis_or_die(config.get(AI_VIS_KEY, "private"),
                                "configuration")
        config[AI_VIS_KEY] = vis_final
        if vis_final != vis:
            print(f"\n({AI_VIS_KEY} resolved to '{vis_final}' — re-running "
                  "preflight for the new mode)")
            vis = vis_final
            findings = doctor(target, layers, vis, manifest)
            n_blockers, n_warns, _ = print_findings(findings)

    for problem in validate_config(config):
        print("WARNING: " + problem, file=sys.stderr)

    plan = adopt_plan(target, config, layers, manifest)
    counts = {}
    for _, action, _ in plan:
        counts[action] = counts.get(action, 0) + 1
    print("\nPlan: " + (", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
                        or "nothing to do"))

    if a.emit_dir:
        emit_dir = os.path.abspath(a.emit_dir)
        written = adopt_emit(emit_dir, target, config, layers)
        print(f"\nRendered {len(written)} file(s) into {emit_dir} "
              "(target untouched).")
        return 1 if n_blockers or (a.strict and n_warns) else 0

    if not a.apply:
        print("\nNothing written — pass --apply to write "
              "(adopt never writes without it).")
        return 1 if n_blockers or (a.strict and n_warns) else 0

    if n_blockers and not a.force:
        print("\nAborted: BLOCKER findings present. Deselect the affected "
              "layer or pass --force.", file=sys.stderr)
        return 1

    actions = adopt_apply(target, plan, layers, manifest, a.overwrite, vis)
    print(f"\nApplied ({len(actions)} entries):")
    for rel in sorted(actions):
        info = actions[rel]
        extra = f" → {info['side']}" if info.get("side") else ""
        print(f"  {info['action']:<12} {rel}{extra}")
    print(f"\nManifest written to {os.path.join(target, ADOPT_MANIFEST)}")
    if "hooks" in layers:
        print("\nHooks were NOT installed (enforcement is opt-in). Next step, "
              "after reviewing scripts/git/:")
        print("  bash scripts/git/install-hooks.sh")
    return 1 if a.strict and n_warns else 0


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "adopt":
        sys.exit(main_adopt(argv[1:]))
    parser = argparse.ArgumentParser(description="Scaffold a project from the startai kit.")
    parser.add_argument("target", nargs="?", help="target directory (default: <product_slug>)")
    parser.add_argument("--config", metavar="FILE", help="load variables from a JSON file and render non-interactively")
    parser.add_argument("--no-review", action="store_true", help="skip the interactive file review")
    parser.add_argument("--dry-run", action="store_true", help="preview the generated project without writing any file")
    parser.add_argument("--dry-run-output", metavar="FILE", help="save the dry-run preview to FILE (default: stdout only)")
    parser.add_argument("--strict", action="store_true", help="fail if the configuration has empty or missing values")
    parser.add_argument("--check", action="store_true", help="validate config.example.json and template/config coherence, then exit")
    args = parser.parse_args()

    if args.check:
        sys.exit(0 if self_check() else 1)

    if args.config:
        config = load_config_file(args.config)
        interactive = False
    else:
        config = wizard(load_defaults())
        interactive = True

    # ai_files_visibility is fatal regardless of --strict.
    config[AI_VIS_KEY] = _vis_or_die(config.get(AI_VIS_KEY), "configuration")

    problems = validate_config(config)
    if problems:
        for problem in problems:
            print("WARNING: " + problem, file=sys.stderr)
        if args.strict:
            print("Error: configuration validation failed (strict mode).", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        dry_run(config, output_path=args.dry_run_output)
        return

    run(args.target, config, do_review=(interactive and not args.no_review))


if __name__ == "__main__":
    main()
