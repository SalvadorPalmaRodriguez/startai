#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# common.sh — Shared functions for all audit checks
# ═══════════════════════════════════════════════════════════════════════════
#
# Functions provided:
#   log_error          — ❌ ERROR (blocking, exit 1 at the end)
#   log_warning        — ⚠️  WARN  (non-blocking unless --strict)
#   log_info           — ℹ️  INFO
#   log_ok             — ✅ OK
#   log_section        — Section header
#   audit_exit         — Final exit with the correct code
#   audit_is_git_repo  — true if PROJECT_ROOT is inside a git work tree
#   audit_source_profile — loads profiles/<name>.conf (checks run as children
#                          of run_all.sh; bash arrays cannot be exported, so
#                          each check re-sources the profile itself)
#
# AUDIT_RESULT contract:
#   audit_exit prints a sentinel line on stdout, without colors, BEFORE exit:
#       AUDIT_RESULT check=<name> errors=<N> warnings=<N> infos=<N>
#   run_all.sh uses it as the source of truth for counters and contrasts the
#   real exit code with the expected one (1 if errors>0; 2 if warnings>0 in
#   strict; 0 otherwise).
#   <name> = ${AUDIT_CHECK_NAME:-$(basename "$0" .sh)}
#
# Expected caller variables:
#   PROJECT_ROOT   — Root of the repo being audited
#   PROFILE        — Profile name (run_all.sh passes it)
#   PROFILE_FILE   — Absolute path to the profile conf (run_all.sh passes it)
#   STRICT         — true/false
#   ERRORS         — Error counter (cumulative)
#   WARNINGS       — Warning counter (cumulative)
#   INFOS          — Info counter (cumulative)
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'; YEL='\033[0;33m'; GRN='\033[0;32m'; BLU='\033[0;34m'; NC='\033[0m'

log_error() {
    ERRORS=$((ERRORS + 1))
    echo -e "  $RED❌ ERROR:$NC $1"
}

log_warning() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "  $YEL⚠️  WARN:$NC $1"
}

log_info() {
    INFOS=$((INFOS + 1))
    echo -e "  $BLUℹ️  INFO:$NC $1"
}

log_ok() {
    echo -e "  $GRN✅$NC $1"
}

log_section() {
    echo -e "\n$BLU── $1 ──$NC"
}

audit_exit() {
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "AUDIT_RESULT check=${AUDIT_CHECK_NAME:-$(basename "$0" .sh)} errors=$ERRORS warnings=$WARNINGS infos=$INFOS"
    if [ "$ERRORS" -gt 0 ]; then
        echo -e "  $RED❌ $ERRORS errors, $WARNINGS warnings, $INFOS infos$NC"
        exit 1
    fi
    if [ "$STRICT" = true ] && [ "$WARNINGS" -gt 0 ]; then
        echo -e "  $YEL⚠️  $WARNINGS warnings (--strict mode)$NC"
        exit 2
    fi
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "  $YEL⚠️  0 errors, $WARNINGS warnings, $INFOS infos$NC"
    else
        echo -e "  $GRN✅ CLEAN AUDIT — 0 errors, 0 warnings$NC"
    fi
    exit 0
}

# True when PROJECT_ROOT is inside a git work tree. Checks that inspect the
# index (git ls-files / staged blobs) must degrade gracefully when the repo
# is not yet under version control.
audit_is_git_repo() {
    git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Re-source the active profile so that its arrays/variables are available.
# run_all.sh exports PROFILE and PROFILE_FILE; standalone runs fall back to
# PROFILE only (resolved relative to the check's own directory).
audit_source_profile() {
    local f="${PROFILE_FILE:-}"
    if [ -z "$f" ] && [ -n "${PROFILE:-}" ]; then
        f="$(cd "$(dirname "${BASH_SOURCE[1]:-$0}")/.." && pwd)/profiles/$PROFILE.conf"
    fi
    if [ -n "$f" ] && [ -f "$f" ]; then
        # shellcheck disable=SC1090
        source "$f"
        return 0
    fi
    return 1
}
