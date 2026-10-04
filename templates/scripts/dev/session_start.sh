#!/usr/bin/env bash
# session_start.sh — Session-context generator for AI agents
#
# Prints a compact summary with everything an agent needs to resume work
# without running discovery commands one by one.
#
# Usage:
#   bash scripts/dev/session_start.sh           # fast mode (default)
#   bash scripts/dev/session_start.sh --deep    # adds extra diagnostics
#
# Output: stdout + /tmp/<repo>_session_context.md (or ~ if /tmp is not writable)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
REPO_NAME="$(basename "$PROJECT_ROOT")"

# ─── Flags ──────────────────────────────────────────────────────────────────
DEEP=false
for arg in "$@"; do
    case "$arg" in
        --deep|-d) DEEP=true ;;
        --help|-h)
            echo "Usage: $0 [--deep]"
            echo "  --deep   Adds an extra diagnostics section (repo size, project hooks)."
            exit 0
            ;;
    esac
done

OUT="/tmp/$REPO_NAME"_session_context.md
if ! touch "$OUT" 2>/dev/null; then
    OUT="$HOME/$REPO_NAME"_session_context.md
    touch "$OUT" || { echo "ERROR: cannot write to /tmp or $HOME"; exit 1; }
fi
START_TS=$(date +%s)

# ─── Helpers ─────────────────────────────────────────────────────────────────
section() { echo "" >> "$OUT"; echo "## $1" >> "$OUT"; echo "" >> "$OUT"; }
kv()      { echo "- **$1**: $2" >> "$OUT"; }
emit()    { echo "$1" >> "$OUT"; }

# ─── Init ────────────────────────────────────────────────────────────────────
cat > "$OUT" << HEADER
# Session context — $REPO_NAME

> **Generated automatically by \`scripts/dev/session_start.sh\`**
> **Read this file IN FULL before running any other command.**
HEADER

# ════════════════════════════════════════════════════════════════════════════
section "1. Environment"
kv "Repo" "$REPO_NAME"
kv "Path" "$PROJECT_ROOT"
kv "Shell" "$SHELL"
kv "User" "$(whoami)"
kv "Date" "$(date '+%Y-%m-%d %H:%M:%S')"
kv "OS" "$(uname -srm)"
command -v python3 > /dev/null 2>&1 && kv "Python" "$(python3 --version 2>&1)"

# ════════════════════════════════════════════════════════════════════════════
section "2. Tests"

# adapta: pick your project's test runner — e.g.
#   make test / cargo test / npm test / python3 -m unittest discover -s tests
TEST_CMD=""
if [ -f Makefile ] && grep -qE '^test:' Makefile; then
    TEST_CMD="make test"
elif [ -f Cargo.toml ]; then
    TEST_CMD="cargo test"
elif [ -f package.json ]; then
    TEST_CMD="npm test"
elif [ -d tests ] && command -v python3 > /dev/null 2>&1; then
    TEST_CMD="python3 -m unittest discover -s tests"
fi

if [ -n "$TEST_CMD" ]; then
    TEST_LOG="$(mktemp)"
    timeout 300 bash -c "$TEST_CMD" > "$TEST_LOG" 2>&1
    TEST_EXIT=$?
    kv "Command" "\`$TEST_CMD\` (exit=$TEST_EXIT)"
    emit '```'
    tail -12 "$TEST_LOG" >> "$OUT"
    emit '```'
    rm -f "$TEST_LOG"
else
    emit "No test runner detected — set TEST_CMD in this script."
fi

# ════════════════════════════════════════════════════════════════════════════
section "3. Coherence (scripts/check.py)"

if [ -f scripts/check.py ]; then
    CHECK_LOG="$(mktemp)"
    python3 scripts/check.py > "$CHECK_LOG" 2>&1
    CHECK_EXIT=$?
    kv "scripts/check.py" "exit=$CHECK_EXIT"
    emit '```'
    tail -10 "$CHECK_LOG" >> "$OUT"
    emit '```'
    rm -f "$CHECK_LOG"
else
    emit "scripts/check.py not found."
fi

# ════════════════════════════════════════════════════════════════════════════
section "4. Git"

if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    emit '```'
    git --no-pager log --oneline --decorate -5 >> "$OUT" 2>/dev/null
    emit '```'
    DIRTY=$(git --no-pager status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    kv "Uncommitted changes" "$DIRTY file(s)"
    if [ "$DIRTY" -gt 0 ]; then
        emit '```'
        git --no-pager status --porcelain 2>/dev/null | head -20 >> "$OUT"
        emit '```'
    fi
else
    emit "Not a git repository."
fi

# ════════════════════════════════════════════════════════════════════════════
section "5. Audit — run_all.sh --profile project"

AUDIT_SCRIPT="$PROJECT_ROOT/scripts/dev/audit/run_all.sh"
if [ -f "$AUDIT_SCRIPT" ]; then
    AUDIT_LOG="$(mktemp)"
    bash "$AUDIT_SCRIPT" --profile project --output "$AUDIT_LOG" > /dev/null 2>&1
    AUDIT_EXIT=$?

    # Aggregated counters + culprit checks, parsed from AUDIT_RESULT sentinels.
    A_ERRORS=0; A_WARNS=0; A_INFOS=0; CULPRITS=""
    while IFS= read -r line; do
        chk=$(printf '%s' "$line" | sed -n 's/^AUDIT_RESULT check=\([^ ]*\).*/\1/p')
        cerr=$(printf '%s' "$line" | sed -n 's/.*errors=\([0-9]*\).*/\1/p')
        cwarn=$(printf '%s' "$line" | sed -n 's/.*warnings=\([0-9]*\).*/\1/p')
        cinfo=$(printf '%s' "$line" | sed -n 's/.*infos=\([0-9]*\).*/\1/p')
        A_ERRORS=$((A_ERRORS + ${cerr:-0}))
        A_WARNS=$((A_WARNS + ${cwarn:-0}))
        A_INFOS=$((A_INFOS + ${cinfo:-0}))
        if [ "${cerr:-0}" -gt 0 ] || [ "${cwarn:-0}" -gt 0 ]; then
            CULPRITS="$CULPRITS $chk(e=$cerr,w=$cwarn)"
        fi
    done < <(grep '^AUDIT_RESULT ' "$AUDIT_LOG" 2>/dev/null)

    kv "audit run_all.sh" "exit=$AUDIT_EXIT — errors=$A_ERRORS, warnings=$A_WARNS, infos=$A_INFOS"
    if [ -n "$CULPRITS" ]; then
        kv "Checks with findings" "$CULPRITS"
        emit ""
        emit '```'
        grep -E '❌ ERROR:|⚠️  WARN:' "$AUDIT_LOG" | head -15 >> "$OUT"
        emit '```'
    fi
    kv "Full transcript" "$AUDIT_LOG"
else
    emit "scripts/dev/audit/run_all.sh not found."
fi

# ════════════════════════════════════════════════════════════════════════════
section "6. Files modified in the last 24h"

emit '```'
find . -type f -mtime -1 \
    -not -path './.git/*' -not -path '*/__pycache__/*' \
    -not -path './node_modules/*' -not -path './target/*' \
    -not -path './.venv/*' -not -path './venv/*' 2>/dev/null \
    | sort | head -25 >> "$OUT"
emit '```'

# ════════════════════════════════════════════════════════════════════════════
#  7. Deep diagnostics — only with --deep
# ════════════════════════════════════════════════════════════════════════════
if $DEEP; then
    section "7. Deep diagnostics (--deep)"
    kv "Repo size" "$(du -sh --exclude=.git --exclude=node_modules --exclude=target . 2>/dev/null | cut -f1)"
    # adapta: add project-specific diagnostics here (linters, doctor commands, ...)
    if command -v gh > /dev/null 2>&1; then
        GH_OWNER=""; GH_REPO=""
        if [ -f config.json ]; then
            GH_OWNER=$(python3 -c "import json;print(json.load(open('config.json')).get('github_user',''))" 2>/dev/null)
            GH_REPO=$(python3 -c "import json;print(json.load(open('config.json')).get('repo',''))" 2>/dev/null)
        fi
        if [ -n "$GH_OWNER" ] && [ -n "$GH_REPO" ] && [ -f scripts/github.py ]; then
            emit ""
            emit "### scripts/github.py status --owner $GH_OWNER --repo $GH_REPO"
            emit '```'
            timeout 20 python3 scripts/github.py status --owner "$GH_OWNER" --repo "$GH_REPO" >> "$OUT" 2>&1 || \
                emit "(github.py status did not complete in 20s)"
            emit '```'
        else
            emit ""
            emit "### gh auth status (no config.json owner/repo for github.py status)"
            emit '```'
            timeout 10 gh auth status >> "$OUT" 2>&1 || emit "(gh not authenticated or timeout)"
            emit '```'
        fi
    else
        emit "\`gh\` not available — GitHub status skipped."
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
END_TS=$(date +%s)
ELAPSED=$(( END_TS - START_TS ))

section "8. Meta"
kv "Generation time" "$ELAPSED s"
kv "Output" "$OUT"
kv "Lines generated" "$(wc -l < "$OUT")"

emit ""
emit "---"
emit "> **INSTRUCTION**: Read this file IN FULL before running any other command."
emit "> Public repo: NEVER commit secrets or private paths (see AGENTS.md)."

# ════════════════════════════════════════════════════════════════════════════
cat "$OUT"
echo ""
echo "✅ Session context generated: $OUT ($(wc -l < "$OUT") lines, $ELAPSED s)"
