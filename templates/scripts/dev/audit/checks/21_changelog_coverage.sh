#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 21_changelog_coverage.sh — CHANGELOG covers the current version
# ═══════════════════════════════════════════════════════════════════════════
#
# Verifies:
#   21.1  The version declared in VERSION_FILE (profile .conf, JSON
#         "version" key — e.g. config.json / config.example.json) has an
#         entry '## [x.y.z]' in CHANGELOG.md.
#   21.2  If the project is a git repo with tags, the highest semver tag
#         also has a CHANGELOG entry.
#
# Prevents releases whose notes say "see CHANGELOG.md" while the CHANGELOG
# lacks the entry.
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "21. CHANGELOG coverage — current version and tags"

CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"
if [ ! -f "$CHANGELOG" ]; then
    log_error "Missing $CHANGELOG"
    audit_exit
fi

# ── 21.1 Declared product version covered ──
echo "── 21.1 Declared version covered by CHANGELOG ──"
VFILE="$PROJECT_ROOT/${VERSION_FILE:-config.json}"
if [ -f "$VFILE" ]; then
    DECLARED=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+[^"]*"' "$VFILE" \
        | head -1 | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)"/\1/')
    if [ -z "$DECLARED" ]; then
        log_warning "$(basename "$VFILE") has no semver \"version\" key — skipped"
    elif grep -qE "^## \[$DECLARED\]" "$CHANGELOG"; then
        log_ok "Declared version $DECLARED has CHANGELOG entry"
    else
        log_error "$(basename "$VFILE") declares $DECLARED but CHANGELOG.md lacks '## [$DECLARED]'"
    fi
else
    log_info "$(basename "$VFILE") not found — skipped (may be gitignored/absent)"
fi

# ── 21.2 Highest git tag covered ──
echo "── 21.2 Highest git tag covered by CHANGELOG ──"
if ! audit_is_git_repo; then
    log_info "Not a git repo — no tags to check"
elif ! LAST_TAG=$(git -C "$PROJECT_ROOT" for-each-ref --sort=-version:refname \
        --format='%(refname:short)' refs/tags 2>/dev/null | head -1) || [ -z "$LAST_TAG" ]; then
    log_info "No published tags — nothing to check"
else
    TAG_VER="${LAST_TAG#v}"
    if grep -qE "^## \[$TAG_VER\]" "$CHANGELOG"; then
        log_ok "Tag $LAST_TAG has entry '## [$TAG_VER]' in CHANGELOG.md"
    else
        log_error "Tag $LAST_TAG has NO entry '## [$TAG_VER]' in CHANGELOG.md — add it before publishing"
    fi
fi

audit_exit
