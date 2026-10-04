#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 23_private_paths.sh — Structural anti-leak protection for private paths
# ═══════════════════════════════════════════════════════════════════════════
#
# Context: the repo is PUBLIC but keeps gitignored private files
# (NOTES.md, MEGAPLAN-*, dev tooling, secrets — plus the AI-context class
# AGENTS.md, .agents/, CLAUDE.md, .claude/ when ai_files_visibility=private).
# `.devinignore` un-ignores them ONLY for agent tools (read/edit) without
# touching .gitignore — git always keeps ignoring them.
#
# What it verifies (offline, deterministic, no network):
#   23.1  Every canonical private pattern is still present as a literal line
#         in .gitignore (worktree). Detects accidental deletions that would
#         open the door to `git add -A` leaking private files.
#   23.2  `git ls-files` contains no private path — detects private files
#         already tracked/staged (the real leak about to be pushed).
#         Degrades to a warning when PROJECT_ROOT is not a git repo yet.
#   23.3  If .gitignore is staged modified, its index blob still keeps all
#         required patterns (worktree alone is not enough).
#   23.4  No .devinignore file negates secrets — negations must only
#         un-ignore private docs/tooling, never keys or credentials.
#   23.5  No forbidden private TERM appears in tracked file contents —
#         terms whose very text is private (trademarks, internal
#         methodology) can't be listed in public files, so they're loaded
#         from a gitignored conf (FORBIDDEN_TERMS_FILE in the profile;
#         STARTAI_PRIVATE_TERMS_FILE env override). Absent/empty → skip.
#
# Policy lives in the profile .conf: REQUIRED_GITIGNORE (literal lines),
# PRIVATE_GLOBS (bash globs, tried verbatim and as "<dir>/**/glob"),
# PUBLIC_EXCEPTIONS (paths public on purpose, e.g. templates/*), and
# DEVINIGNORE_FILES (every ignore-file for agent tools to audit).
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "23. Private paths (structural anti-leak)"

is_private_path() {
    local f="$1" g
    # Public exceptions first (e.g. templates/* ships public on purpose).
    for g in "${PUBLIC_EXCEPTIONS[@]:-}"; do
        [[ "$f" == $g ]] && return 1
    done
    for g in "${PRIVATE_GLOBS[@]:-}"; do
        # verbatim match, plus "<dir>/**/glob" (unanchored .gitignore
        # semantics: a pattern without leading '/' matches at any level)
        [[ "$f" == $g || "$f" == */$g ]] && return 0
    done
    return 1
}

# ── 23.1 Required patterns present in .gitignore (worktree) ──
echo "── 23.1 Private patterns present in .gitignore ──"
if [ ! -f "$PROJECT_ROOT/.gitignore" ]; then
    log_error "Missing $PROJECT_ROOT/.gitignore — no anti-leak protection"
else
    MISSING=()
    for pat in "${REQUIRED_GITIGNORE[@]:-}"; do
        grep -Fxq "$pat" "$PROJECT_ROOT/.gitignore" 2>/dev/null || MISSING+=("$pat")
    done
    if [ "${#MISSING[@]}" -gt 0 ]; then
        log_error ".gitignore lost ${#MISSING[@]} private pattern(s):"
        printf '    %s\n' "${MISSING[@]}"
    else
        log_ok ".gitignore keeps the ${#REQUIRED_GITIGNORE[@]} private patterns"
    fi
fi

# ── 23.2 No private path tracked/staged (git ls-files) ──
echo "── 23.2 Private paths in the git index ──"
if audit_is_git_repo; then
    LEAKED=()
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        is_private_path "$f" && LEAKED+=("$f")
    done < <(cd "$PROJECT_ROOT" && git ls-files)
    if [ "${#LEAKED[@]}" -gt 0 ]; then
        log_error "${#LEAKED[@]} PRIVATE path(s) tracked/staged — leak to public repo:"
        printf '    %s\n' "${LEAKED[@]:0:10}"
        echo "    Fix: git rm --cached <path>  (and check if it was already pushed)" >&2
    else
        log_ok "No private path in git ls-files"
    fi
else
    log_warning "Not a git repo — skipping git index checks (23.2/23.3)"
fi

# ── 23.3 Staged .gitignore blob keeps the patterns ──
echo "── 23.3 Staged .gitignore blob (if in the index) ──"
if audit_is_git_repo; then
    if (cd "$PROJECT_ROOT" && git diff --cached --name-only | grep -qx '.gitignore'); then
        STAGED_GI="$(cd "$PROJECT_ROOT" && git show ':.gitignore' 2>/dev/null || true)"
        STAGED_MISSING=()
        for pat in "${REQUIRED_GITIGNORE[@]:-}"; do
            printf '%s\n' "$STAGED_GI" | grep -Fxq "$pat" || STAGED_MISSING+=("$pat")
        done
        if [ "${#STAGED_MISSING[@]}" -gt 0 ]; then
            log_error "The STAGED .gitignore drops ${#STAGED_MISSING[@]} private pattern(s):"
            printf '    %s\n' "${STAGED_MISSING[@]}"
            echo "    Restore the patterns before committing (was it relaxed" >&2
            echo "    for a workflow and never reverted?)." >&2
        else
            log_ok "Staged .gitignore keeps all private patterns"
        fi
    else
        log_ok ".gitignore is not staged — nothing to check"
    fi
fi

# ── 23.4 No .devinignore negates secrets ──
echo "── 23.4 .devinignore negations (never secrets) ──"
CHECKED=0
for rel in "${DEVINIGNORE_FILES[@]:-.devinignore}"; do
    f="$PROJECT_ROOT/$rel"
    [ -f "$f" ] || continue
    CHECKED=$((CHECKED + 1))
    BAD_NEG=$(grep -nE '^!' "$f" \
        | grep -iE 'key|pem|p12|pfx|env|secret|session\.json|providers\.|credential|passwd' \
        || true)
    if [ -n "$BAD_NEG" ]; then
        log_error "$rel un-ignores possible secrets (agent tools would read them):"
        printf '    %s\n' "$BAD_NEG"
    else
        log_ok "$rel only negates private paths, not secrets"
    fi
done
[ "$CHECKED" -eq 0 ] && log_ok "No .devinignore files — nothing to check"

# ── 23.5 No forbidden private term in tracked files ──
echo "── 23.5 Forbidden private terms in tracked files ──"
TERMS_PATH="${STARTAI_PRIVATE_TERMS_FILE:-${FORBIDDEN_TERMS_FILE:-}}"
[ -n "$TERMS_PATH" ] && [[ "$TERMS_PATH" != /* ]] \
    && TERMS_PATH="$PROJECT_ROOT/$TERMS_PATH"
if [ -z "$TERMS_PATH" ] || [ ! -f "$TERMS_PATH" ]; then
    log_info "No forbidden-terms file configured/present — skipped"
elif ! audit_is_git_repo; then
    log_warning "Not a git repo — skipping tracked-file term scan"
else
    TERMS_RE=$(grep -vE '^[[:space:]]*(#|$)' "$TERMS_PATH" | paste -sd'|' -)
    if [ -z "$TERMS_RE" ]; then
        log_info "Forbidden-terms file has no active terms — nothing to scan"
    else
        TERM_HITS=()
        while IFS= read -r f; do
            [ -n "$f" ] && TERM_HITS+=("$f")
        done < <(cd "$PROJECT_ROOT" && git grep -liIE "$TERMS_RE" -- . 2>/dev/null || true)
        if [ "${#TERM_HITS[@]}" -gt 0 ]; then
            log_error "${#TERM_HITS[@]} tracked file(s) contain a forbidden private term:"
            printf '    %s\n' "${TERM_HITS[@]:0:10}"
            echo "    The term itself is private — it must not live in any" >&2
            echo "    versioned file. Remove it or load it from a gitignored" >&2
            echo "    conf at runtime (see forbidden-terms.conf convention)." >&2
        else
            log_ok "No forbidden private terms in tracked files"
        fi
    fi
fi

audit_exit
