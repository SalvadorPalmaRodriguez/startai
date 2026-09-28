#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 19_version_sync.sh — Product version propagated to public consumers
# ═══════════════════════════════════════════════════════════════════════════
#
# Canonical source: the first '## [x.y.z]' heading in CHANGELOG.md
# (Keep-a-Changelog format; 'Unreleased' is ignored).
#
# VERSION_TARGETS (profile .conf): entries "path:kind"
#   json_version     — file must contain  "version": "<ver>"
#   badge_version    — file must contain  version-<ver>   (shields.io badge)
#   current_version  — file must contain  Current version: <ver>
#
# Missing file → warning (e.g. gitignored config.json may be absent).
# Present file without the pattern → warning. Wrong value → error.
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "19. Version sync (canonical: CHANGELOG.md)"

CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"
if [ ! -f "$CHANGELOG" ]; then
    log_error "Missing $CHANGELOG — no canonical version source"
    audit_exit
fi

CANON_VER=$(grep -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+[^]]*\]' "$CHANGELOG" \
    | head -1 | sed -E 's/^## \[([^]]+)\]/\1/')

if [ -z "$CANON_VER" ]; then
    log_error "No '## [x.y.z]' entry found in CHANGELOG.md"
    audit_exit
fi
log_info "Canonical version (CHANGELOG.md): $CANON_VER"

for spec in ${VERSION_TARGETS[@]+"${VERSION_TARGETS[@]}"}; do
    file="${spec%%:*}"
    kind="${spec#*:}"
    path="$PROJECT_ROOT/$file"

    if [ ! -f "$path" ]; then
        log_warning "$file not found — skipped ($kind)"
        continue
    fi

    case "$kind" in
        json_version)
            val=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' "$path" \
                | head -1 | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)"/\1/')
            if [ -z "$val" ]; then
                log_warning "$file has no \"version\" key"
            elif [ "$val" != "$CANON_VER" ]; then
                log_error "Version drift: $file=$val vs CHANGELOG=$CANON_VER"
            else
                log_ok "$file version = $val"
            fi
            ;;
        badge_version)
            if grep -qE "version-$CANON_VER([^0-9]|$)" "$path"; then
                log_ok "$file badge shows $CANON_VER"
            elif grep -oE 'version-[0-9]+\.[0-9]+\.[0-9]+[^)]*' "$path" | head -1 | grep -q .; then
                other=$(grep -oE 'version-[0-9]+\.[0-9]+\.[0-9]+' "$path" | head -1)
                log_error "Version drift: $file badge=$other vs CHANGELOG=$CANON_VER"
            else
                log_warning "$file has no version badge (expected version-$CANON_VER)"
            fi
            ;;
        current_version)
            if grep -qE "Current version: $CANON_VER([^0-9]|$)" "$path"; then
                log_ok "$file declares 'Current version: $CANON_VER'"
            elif grep -oE 'Current version: [0-9]+\.[0-9]+\.[0-9]+' "$path" | head -1 | grep -q .; then
                other=$(grep -oE 'Current version: [0-9]+\.[0-9]+\.[0-9]+' "$path" | head -1)
                log_error "Version drift: $file '$other' vs CHANGELOG=$CANON_VER"
            else
                log_warning "$file has no 'Current version:' line"
            fi
            ;;
        *)
            log_warning "Unknown VERSION_TARGETS kind '$kind' in $spec"
            ;;
    esac
done

audit_exit
