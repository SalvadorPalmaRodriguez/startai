#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 04_web_links.sh — Broken relative links in public Markdown
# ═══════════════════════════════════════════════════════════════════════════
#
# Scans the Markdown files selected by the profile (MD_SCAN_DIRS +
# MD_SCAN_FILES) and verifies that every relative link/image target resolves
# to a real file or directory.
#
#   04.1  Relative link/image targets exist (missing target → error).
#   04.2  Same-document anchors (#frag) resolve to a heading — only for
#         root-level .md files (GitHub-rendered; docs/ is rendered by Jekyll
#         with a different slugger, so anchors there are not checked).
#         Missing anchor → warning.
#
# HTML comments <!-- ... --> and fenced code blocks ``` ... ``` are stripped
# BEFORE extracting links: READMEs intentionally keep commented-out blocks
# (e.g. the demo GIF) and docs embed illustrative link syntax in examples;
# neither must produce false positives.
#
# External URLs (http(s):, mailto:, //, tel:) and absolute paths are skipped
# (offline check — no network).
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "04. Markdown links (relative targets)"

# ── Collect the markdown file list from the profile ──
MD_LIST=()
for d in "${MD_SCAN_DIRS[@]:-}"; do
    [ -d "$PROJECT_ROOT/$d" ] || continue
    while IFS= read -r f; do
        MD_LIST+=("$f")
    done < <(find "$PROJECT_ROOT/$d" -type f -name '*.md' | sort)
done
for f in "${MD_SCAN_FILES[@]:-}"; do
    [ -f "$PROJECT_ROOT/$f" ] && MD_LIST+=("$PROJECT_ROOT/$f")
done

if [ "${#MD_LIST[@]}" -eq 0 ]; then
    log_warning "No markdown files found (profile MD_SCAN_*)"
    audit_exit
fi
log_info "Markdown files scanned: ${#MD_LIST[@]}"

# ── Python does the parsing; prints TSV findings to stdout ──
FINDINGS=$(PROJECT_ROOT="$PROJECT_ROOT" python3 - "${MD_LIST[@]}" <<'PYEOF'
import os, re, sys, unicodedata

root = os.environ["PROJECT_ROOT"]
files = sys.argv[1:]

# Strip HTML comments (<!-- ... -->) and fenced code blocks (``` / ~~~)
# before extracting links: READMEs keep commented-out blocks on purpose
# (demo GIF, badges), and docs embed illustrative link syntax inside code
# fences — neither is a real navigable link.
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.DOTALL | re.MULTILINE)

def strip_noise(text):
    return FENCE_RE.sub("", COMMENT_RE.sub("", text))
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)[^)]*\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)

def gh_slug(text):
    """GitHub-style anchor slug: lowercase, drop chars that are not
    letter/number/space/hyphen/underscore, spaces -> '-'."""
    t = unicodedata.normalize("NFKC", text.strip().lower())
    t = "".join(c for c in t
                if c.isalnum() or c in (" ", "-", "_"))
    return t.replace(" ", "-")

slug_cache = {}
def anchors_of(path):
    if path in slug_cache:
        return slug_cache[path]
    try:
        body = open(path, encoding="utf-8").read()
    except OSError:
        slug_cache[path] = set()
        return slug_cache[path]
    body = strip_noise(body)
    slugs = {gh_slug(m.group(1)) for m in HEADING_RE.finditer(body)}
    slug_cache[path] = slugs
    return slugs

for md in files:
    try:
        raw = open(md, encoding="utf-8").read()
    except OSError:
        print("E\t%s\t%s" % (md, "<unreadable>"))
        continue
    body = strip_noise(raw)
    rel = os.path.relpath(md, root)
    for m in LINK_RE.finditer(body):
        target = m.group(1).strip()
        if not target or target.startswith((
                "http://", "https://", "mailto:", "tel:", "//")):
            continue
        path_part, _, frag = target.partition("#")
        path_part = path_part.split("?", 1)[0]
        if path_part.startswith("/"):
            continue  # absolute site path — Jekyll resolves it at build time
        if path_part:
            dest = os.path.normpath(os.path.join(os.path.dirname(md), path_part))
            if not (os.path.isfile(dest) or os.path.isdir(dest)):
                # .md extension implied (docs sometimes omit it)
                if not os.path.isfile(dest + ".md"):
                    print("E\t%s\t%s" % (rel, target))
                    continue
        else:
            dest = md  # pure #fragment → same document
        if frag and dest.endswith(".md") and os.path.dirname(dest) == root:
            # Anchor check only for GitHub-rendered root docs
            if frag.lower() not in anchors_of(dest):
                print("A\t%s\t%s" % (rel, target))
print("I\t-")
PYEOF
)

N_ERR=0; N_ANCH=0
while IFS=$'\t' read -r kind file link; do
    case "$kind" in
        E) log_error "Broken link in $file → $link"; N_ERR=$((N_ERR + 1)) ;;
        A) log_warning "Unresolved anchor in $file → $link"; N_ANCH=$((N_ANCH + 1)) ;;
        I) : ;;
    esac
done <<< "$FINDINGS"

[ "$N_ERR" -eq 0 ] && log_ok "All relative markdown targets resolve"
[ "$N_ANCH" -eq 0 ] && log_ok "All root-document anchors resolve"

audit_exit
