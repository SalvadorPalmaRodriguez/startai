#!/usr/bin/env python3
"""check.py — project coherence checks (self-contained, no external deps).

Validates:
  1. config.json (if present) is valid JSON with no empty string values.
  2. No unresolved placeholders in text files: neither double-brace tokens
     nor legacy single-brace ALL-CAPS tokens
     (the Jekyll layout and this file itself are skipped).
  3. Bilingual docs parity: every docs/en/*.md has a docs/es/*.md counterpart and vice versa.

Exit 0 if OK, 1 otherwise.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_SUFFIXES = (".md", ".txt", ".yml", ".yaml", ".json", ".toml",
                 ".html", ".css", ".svg", ".sh", ".py", ".gitignore", ".devinignore")

SKIP_DIRS = {".git", "__pycache__", "node_modules", "target", "venv", ".venv"}

# Files that legitimately contain brace patterns:
#   - docs/_layouts/default.html — Jekyll/Liquid tags {{ page.* }}
#   - scripts/check.py — this file holds the placeholder patterns themselves
SKIP_TOKEN_FILES = {"docs/_layouts/default.html", "scripts/check.py"}

# ai_files_visibility enum — anything outside it is a hard error (a typo
# must never silently pick a privacy policy).
AI_VIS_KEY = "ai_files_visibility"
AI_VIS_MODES = ("private", "public")

TOKEN_RE = re.compile(r"\{\{\w+\}\}")

# Legacy single-brace ALL-CAPS placeholder style. Any
# document that still uses it ships unfilled placeholders invisible to the
# double-brace check above. Spaced references like `{{ key }}` are allowed:
# they are documentation of the convention, not real placeholders.
LEGACY_TOKEN_RE = re.compile(r"\{[A-Z][A-Z_]{2,}\}|\{YYYY-MM-DD\}")


def _problems_visibility(value, source):
    if value is None:
        return []
    if str(value).strip().lower() not in AI_VIS_MODES:
        return [f"{source}: invalid {AI_VIS_KEY}={value!r} "
                f"(expected {'|'.join(AI_VIS_MODES)})"]
    return []


def problems_config():
    problems = []
    cfg_path = os.path.join(ROOT, "config.json")
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        for key, value in data.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                problems.append(f"config.json: empty value for {key}")
        problems += _problems_visibility(data.get(AI_VIS_KEY), "config.json")
    man_path = os.path.join(ROOT, ".startai-adopt.json")
    if os.path.isfile(man_path):
        try:
            with open(man_path, encoding="utf-8") as f:
                mdata = json.load(f)
        except (OSError, json.JSONDecodeError):
            mdata = None
        if isinstance(mdata, dict):
            problems += _problems_visibility(
                mdata.get(AI_VIS_KEY), ".startai-adopt.json")
    return problems


def problems_tokens():
    problems = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(TEXT_SUFFIXES):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, ROOT)
            if rel in SKIP_TOKEN_FILES:
                continue
            try:
                content = open(path, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for token in TOKEN_RE.findall(content):
                problems.append(f"unresolved token in {rel}: {token}")
            for token in LEGACY_TOKEN_RE.findall(content):
                problems.append(f"legacy single-brace placeholder in {rel}: {token}")
    return problems


def problems_bilingual():
    problems = []
    en_dir = os.path.join(ROOT, "docs", "en")
    es_dir = os.path.join(ROOT, "docs", "es")
    if not (os.path.isdir(en_dir) and os.path.isdir(es_dir)):
        return problems
    en = {f for f in os.listdir(en_dir) if f.endswith(".md")}
    es = {f for f in os.listdir(es_dir) if f.endswith(".md")}
    for f in sorted(en - es):
        problems.append(f"docs/en/{f} has no docs/es/{f} counterpart")
    for f in sorted(es - en):
        problems.append(f"docs/es/{f} has no docs/en/{f} counterpart")
    return problems


def main():
    problems = problems_config() + problems_tokens() + problems_bilingual()
    if problems:
        for p in problems:
            print("ERROR: " + p, file=sys.stderr)
        sys.exit(1)
    print("OK: project is coherent.")
    sys.exit(0)


if __name__ == "__main__":
    main()
