#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 24_public_doc_refs.sh — Private-path references inside PUBLIC docs
# ═══════════════════════════════════════════════════════════════════════════
#
# The public docs (README, docs/) are served and shipped verbatim; a pointer
# to a gitignored private path (.agents/, scripts/dev/, docs/dev/…) leaks the
# private repo structure AND is a broken reference for the public reader.
#
# Two rules, both ERROR (anti-leak, same category as check 23):
#   R1 — a private path in a doc's "> **References:**" / "> **Referencias:**"
#        header line: ERROR, no exceptions. A references header promises a
#        readable file.
#   R2 — a private path anywhere else in a public doc: ERROR, unless the file
#        is in PUBLIC_DOC_PRIVATE_REF_ALLOW.
#
# Scope: MD_SCAN_DIRS + MD_SCAN_FILES from the profile, excluding templates/
# (template content legitimately contains those paths — it IS the product).
#
# Needles are DERIVED from PRIVATE_GLOBS (single source of private paths —
# never duplicate the list). Transformation:
#   - "X/*" directory globs  → searchable prefix "X/"  (.agents/, docs/dev/…)
#   - literals without glob chars that start with '.' or contain '/'
#                            → used verbatim (.devinignore, .env, …)
#   - everything else (AGENTS.md, *.key, MEGAPLAN-*.md, bare names) is
#     skipped: not a valid text needle, or legitimately referenced in public
#     prose (AGENTS.md lives at the public repo root).
#
# Allowlist trade-off (accepted on purpose): a NEW private-path leak inside
# an allowlisted file goes undetected. Accepted because those files document
# the pattern by definition (the AI-native tutorial, the README structure
# tables) — removing the references would gut the doc.
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "24. Private-path references in public docs"

# ── Build searchable needles from PRIVATE_GLOBS (see header) ──
NEEDLE_RE=$(
    for g in "${PRIVATE_GLOBS[@]:-}"; do
        case "$g" in
            */\*)       printf '%s\n' "${g%/*}/" ;;   # "X/*" -> "X/"
            *[*?]* | *\[*) : ;;                        # other globs: no needle
            .* | */* )  printf '%s\n' "$g" ;;          # dotfiles / path literals
        esac
    done | sort -u | sed 's/[][\.*^$/]/\\&/g' | paste -sd'|' -
)

if [ -z "$NEEDLE_RE" ]; then
    log_warning "No searchable private paths derivable from PRIVATE_GLOBS"
    audit_exit
fi

# ── Collect public docs in scope (templates/ excluded) ──
SCAN_FILES=()
for d in "${MD_SCAN_DIRS[@]:-}"; do
    [ -d "$PROJECT_ROOT/$d" ] || continue
    while IFS= read -r f; do
        SCAN_FILES+=("$f")
    done < <(find "$PROJECT_ROOT/$d" -type f \( -name '*.md' -o -name '*.txt' \) \
        ! -path '*/templates/*')
done
for f in "${MD_SCAN_FILES[@]:-}"; do
    [ -f "$PROJECT_ROOT/$f" ] && SCAN_FILES+=("$PROJECT_ROOT/$f")
done

is_allowed() {
    local rel="$1" a
    for a in "${PUBLIC_DOC_PRIVATE_REF_ALLOW[@]:-}"; do
        [ "$rel" = "$a" ] && return 0
    done
    return 1
}

# ── R1 + R2 scan ──
R1_HITS=()
R2_HITS=()
for f in "${SCAN_FILES[@]:-}"; do
    [ -n "$f" ] || continue
    rel="${f#$PROJECT_ROOT/}"
    while IFS= read -r hit; do
        line="${hit#*:*:}"   # hit is "rel:lineno:content"
        if printf '%s' "$line" | grep -qE '^> *\*\*(References|Referencias):\*\*'; then
            R1_HITS+=("$hit")
        elif ! is_allowed "$rel"; then
            R2_HITS+=("$hit")
        fi
    done < <(grep -nE "$NEEDLE_RE" "$f" 2>/dev/null | sed "s|^|$rel:|" || true)
done

if [ "${#R1_HITS[@]}" -gt 0 ]; then
    log_error "${#R1_HITS[@]} private path(s) in References header lines:"
    printf '    %s\n' "${R1_HITS[@]:0:10}" | sed "s|$PROJECT_ROOT/||"
fi
if [ "${#R2_HITS[@]}" -gt 0 ]; then
    log_error "${#R2_HITS[@]} private path reference(s) in public docs:"
    printf '    %s\n' "${R2_HITS[@]:0:10}" | sed "s|$PROJECT_ROOT/||"
    echo "    Cite skills by name, never by private path; or allowlist the" >&2
    echo "    file in PUBLIC_DOC_PRIVATE_REF_ALLOW if it documents the pattern." >&2
fi
if [ "${#R1_HITS[@]}" -eq 0 ] && [ "${#R2_HITS[@]}" -eq 0 ]; then
    log_ok "No private-path references in public docs"
fi

audit_exit
