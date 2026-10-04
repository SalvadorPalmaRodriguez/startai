#!/usr/bin/env python3
"""context-gen.py — flatten a repository into a single context file for LLMs.

Adapted from a repo flattener (GitCodeFlattener), hardened:

  - recursive walk filtered by extension/exact-name, --ignore-dirs
  - skips ALL hidden entries (.*) — INCLUDING .env
    (the original skipped every hidden file EXCEPT .env and its own test
    asserted that SECRET=123 reached the output; that leak is inverted here)
  - denylist of secret filenames/paths that are never exported; the only
    override is the explicit --i-know-this-leaks-secrets flag
  - scans the composed output for credential patterns before writing:
    on any hit the file is NOT written and the tool exits 1
  - atomic write (<out>.tmp + os.replace); the default output lives OUTSIDE
    the source tree

Usage:
    context-gen.py --root <dir> [--extensions <e1,e2>] [--ignore-dirs <d1,d2>]
                   [--output <file>] [--i-know-this-leaks-secrets]

Only the Python standard library is used.
"""

import argparse
import fnmatch
import os
import re
import sys
import tempfile

DEFAULT_EXTENSIONS = ".md,.txt,.py,.sh,.json,.yml,.yaml,.toml,.html,.css,.rs"
DEFAULT_IGNORE_DIRS = ".git,target,node_modules,__pycache__,dist,build"

# Paths that are never exported. fnmatch patterns matched against the
# basename of every file AND directory (a denied directory is not entered).
# 'config.json' is denied because scaffolded projects keep real owner/email
# there. Note: hidden files (.env included) are already excluded by the
# hidden-entry rule — this list additionally covers non-hidden secrets such
# as credentials.txt or deploy/key.pem.
DENY_PATTERNS = [
    ".env",
    ".env.*",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "minisign.key",
    "config.json",
    "credentials*",
    "*.secret",
    "id_rsa",
    "id_ed25519",
    "secrets.*",
    "*.keystore",
]

# Minimal subset of the audit check 01_secrets_and_creds patterns, applied
# to the composed output before it is written. Anchored enough to not match
# the regex literals that this very file (or the audit check itself) carries.
SECRET_RES = [
    ("PEM private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GCP API key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("GitHub token", re.compile(r"g[hpousr]_[A-Za-z0-9]{20,}")),
    ("API key (sk-...)", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}")),
    ("password assignment", re.compile(r"password\s*=\s*[\"']?[^\s\"'<{$]{4,}", re.IGNORECASE)),
]


def parse_list(value):
    return [item.strip().lstrip(".") for item in value.split(",") if item.strip()]


def is_denied(name):
    lname = name.lower()
    return any(fnmatch.fnmatch(lname, pat.lower()) for pat in DENY_PATTERNS)


def collect_files(root, ext_set, ignore_set, out_path):
    """Walk root and yield (rel_path, content) for includable UTF-8 files."""
    files = []
    for current, dirs, names in os.walk(root):
        dirs.sort()
        # Prune hidden dirs, ignored dirs and denied dirs, in place.
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in ignore_set
            and not is_denied(d)
        ]
        for name in sorted(names):
            if name.startswith("."):
                continue
            path = os.path.join(current, name)
            rel = os.path.relpath(path, root)
            if out_path is not None and os.path.abspath(path) == out_path:
                continue
            stem, dot, ext = name.rpartition(".")
            if ext not in ext_set and name not in ext_set:
                continue
            if is_denied(name):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, OSError):
                continue  # non-UTF-8 or unreadable — silently skipped
            files.append((rel, content))
    return files


def compose(root, files):
    lines = [
        "# Project Context Export",
        f"# Source: {root}",
        f"# Files: {len(files)}",
        "# Content:",
        "",
    ]
    for rel, content in files:
        lines.append(f'<file path="{rel}">')
        lines.append(content)
        lines.append("</file>")
        lines.append("")
    return "\n".join(lines)


def scan_output(text):
    """Return [(pattern_name, lineno, line)] for each credential-looking hit."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, regex in SECRET_RES:
            if regex.search(line):
                hits.append((name, lineno, line.strip()[:120]))
    return hits


def main():
    parser = argparse.ArgumentParser(
        description="Flatten a repository into a single context file for LLMs."
    )
    parser.add_argument("--root", required=True, help="repository root directory")
    parser.add_argument("--extensions", default=DEFAULT_EXTENSIONS,
                        help="comma-separated extensions or exact filenames "
                             "(default: %(default)s)")
    parser.add_argument("--ignore-dirs", default=DEFAULT_IGNORE_DIRS,
                        help="comma-separated directory names to skip "
                             "(default: %(default)s)")
    parser.add_argument("--output", default=None,
                        help="output file (default: /tmp/context-<repo>.txt)")
    parser.add_argument("--i-know-this-leaks-secrets", action="store_true",
                        help="disable the secret denylist and the pre-write "
                             "scan. Hidden files (.*) are still skipped.")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"❌ Error: --root is not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    ext_set = set(parse_list(args.extensions))
    ignore_set = set(parse_list(args.ignore_dirs))
    leaks_ok = args.i_know_this_leaks_secrets

    if args.output:
        out_path = os.path.abspath(args.output)
    else:
        base = os.path.join(tempfile.gettempdir(), f"context-{os.path.basename(root)}.txt")
        out_path = os.path.abspath(base)
        if not os.access(os.path.dirname(out_path) or ".", os.W_OK):
            out_path = os.path.abspath(
                os.path.join(os.path.expanduser("~"), f"context-{os.path.basename(root)}.txt"))

    inside_root = os.path.commonpath([root, out_path]) == root
    if inside_root:
        print(f"⚠️  Aviso: --output está dentro del árbol de fuentes: {out_path}",
              file=sys.stderr)

    files = collect_files(root, ext_set, ignore_set,
                          out_path if inside_root else None)
    output = compose(root, files)

    hits = scan_output(output)
    if hits:
        print("❌ La salida contiene patrones de credenciales:", file=sys.stderr)
        for name, lineno, line in hits[:20]:
            print(f"   [{name}] línea {lineno}: {line}", file=sys.stderr)
        if not leaks_ok:
            print("   No se escribe el fichero. Para forzarlo: --i-know-this-leaks-secrets",
                  file=sys.stderr)
            sys.exit(1)
        print("   ⚠️  --i-know-this-leaks-secrets: se escribe igualmente.", file=sys.stderr)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(output)
    os.replace(tmp_path, out_path)

    print(f"✅ Contexto generado: {out_path} ({len(files)} ficheros)")


if __name__ == "__main__":
    main()
