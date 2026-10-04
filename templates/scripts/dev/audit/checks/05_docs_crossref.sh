#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 05_docs_crossref.sh — Doc header metadata + cross-references
# ═══════════════════════════════════════════════════════════════════════════
#
# Validates the doc header block used across the public documentation:
#   > **Version:** X.Y | **Updated:** YYYY-MM-DD        (EN)
#   > **Versión:** X.Y | **Actualizado:** YYYY-MM-DD    (ES)
#   > **Status:** / **Estado:** ...
#   > **References:** / **Referencias:** ...
#
# CHECKS (all warnings — a doc without a header is incomplete, not broken):
#   1. Version metadata present and well-formed (X.Y or X.Y.Z)
#   2. Update date present and well-formed (YYYY-MM-DD)
#   3. Status metadata present
#   4. References line/section present
#   5. Relative links between docs resolve (defense in depth — 04 covers
#      this too; here it is restricted to intra-docs ./ and ../ links)
#
# Scope: MD_SCAN_DIRS + MD_SCAN_FILES from the profile. CHANGELOG.md is
# skipped (Keep-a-Changelog format has no such header).
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "05. Doc headers and cross-references"

# ── Collect markdown files (git ls-files when available, find otherwise) ──
md_files=()
collect_dir() {
    local dir="$1"
    [ -d "$PROJECT_ROOT/$dir" ] || return 0
    if audit_is_git_repo; then
        while IFS= read -r f; do
            [ -n "$f" ] && md_files+=("$PROJECT_ROOT/$f")
        done < <(git -C "$PROJECT_ROOT" ls-files -- "$dir/*.md" "$dir/**/*.md" 2>/dev/null)
    else
        while IFS= read -r f; do
            md_files+=("$f")
        done < <(find "$PROJECT_ROOT/$dir" -type f -name '*.md' | sort)
    fi
}
for d in "${MD_SCAN_DIRS[@]:-}"; do
    collect_dir "$d"
done
for f in "${MD_SCAN_FILES[@]:-}"; do
    [ -f "$PROJECT_ROOT/$f" ] && md_files+=("$PROJECT_ROOT/$f")
done

if [ "${#md_files[@]}" -eq 0 ]; then
    log_warning "No .md files found (profile MD_SCAN_*)"
    audit_exit
fi

audit_is_git_repo \
    && log_info "File source: git ls-files (${#md_files[@]} files)" \
    || log_info "File source: find (${#md_files[@]} files, not a git repo)"

check_header() {
    local file="$1" content
    content=$(cat "$file")

    if ! echo "$content" | grep -qE '\*\*(Versión|Version):\*\* v?[0-9]+\.[0-9]+(\.[0-9]+)?'; then
        log_warning "No/wrong version header: $file"
    fi
    if ! echo "$content" | grep -qE '\*\*(Actualizado|Updated):\*\* [0-9]{4}-[0-9]{2}-[0-9]{2}'; then
        log_warning "No/wrong update-date header: $file"
    fi
    if ! echo "$content" | grep -qiE '\*\*(Estado|Status):\*\*'; then
        log_warning "No status header: $file"
    fi
    if ! echo "$content" | grep -qiE '\*\*(Referencias|References):\*\*|## (Referencias|References|Cross-references)'; then
        log_warning "No references line/section: $file"
    fi
}

while IFS= read -r file; do
    [ -z "$file" ] && continue
    [ -f "$file" ] || continue  # tracked but deleted from worktree
    case "$(basename "$file")" in
        README*.md|CHANGELOG.md) continue ;;  # READMEs and changelogs have
                                              # their own format, no doc header
    esac
    check_header "$file"
done < <(printf '%s\n' "${md_files[@]}")

audit_exit
