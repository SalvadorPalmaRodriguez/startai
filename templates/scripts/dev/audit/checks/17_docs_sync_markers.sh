#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 17_docs_sync_markers.sh — Pending-work markers in public docs
# ═══════════════════════════════════════════════════════════════════════════
#
# Flags [PENDIENTE] / [PENDING] / FIXME / TODO markers left in the public
# documentation surface. A marker means the doc promises something the code
# has not delivered yet — it should be removed once implemented (DOC-SYNC).
#
# Scope: MARKER_SCAN_DIRS + MARKER_SCAN_FILES from the profile, restricted to
# .md/.txt files (public documentation only).
# Severity: warning (a reminder, not breakage).
#
# MARKER_IGNORE_RE (optional, extended regex): hit lines matching it are
# filtered BEFORE counting — for self-referential mentions, i.e. docs that
# describe the marker convention itself. Trade-off, accepted on purpose: a
# real pending marker written inside backticks would be filtered too. Backticks
# signal "I am talking about the literal token", while real pending work is
# written in plain prose — and a false negative here only downgrades a
# reminder, it does not hide breakage.
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "17. Pending-work markers in public docs"

SCAN_TARGETS=()
for d in "${MARKER_SCAN_DIRS[@]:-}"; do
    [ -d "$PROJECT_ROOT/$d" ] && SCAN_TARGETS+=("$PROJECT_ROOT/$d")
done
for f in "${MARKER_SCAN_FILES[@]:-}"; do
    [ -f "$PROJECT_ROOT/$f" ] && SCAN_TARGETS+=("$PROJECT_ROOT/$f")
done

if [ "${#SCAN_TARGETS[@]}" -eq 0 ]; then
    log_warning "No scan targets found (profile MARKER_SCAN_*)"
    audit_exit
fi

# '[PENDIENTE]'/'[PENDING]' style markers and bare FIXME/TODO comments.
# NOTE: this file itself contains those literals in the regex below; docs
# scan only reaches .md/.txt so there is no self-match.
HITS=$(grep -rnE '\[(PENDIENTE|PENDING)\]|FIXME|TODO:' \
    "${SCAN_TARGETS[@]}" --include='*.md' --include='*.txt' 2>/dev/null \
    || true)

# Filter out self-referential mentions (see header trade-off note).
# Empty/unset MARKER_IGNORE_RE => no filtering (backwards compatible).
if [ -n "$HITS" ] && [ -n "${MARKER_IGNORE_RE:-}" ]; then
    HITS=$(printf '%s\n' "$HITS" | grep -vE "$MARKER_IGNORE_RE" || true)
fi

if [ -n "$HITS" ]; then
    COUNT=$(echo "$HITS" | wc -l | tr -d ' ')
    log_warning "Pending markers found in public docs: $COUNT"
    echo "$HITS" | sed "s|$PROJECT_ROOT/||" | head -10 | sed 's/^/    /'
else
    log_ok "No pending markers in public docs"
fi

audit_exit
