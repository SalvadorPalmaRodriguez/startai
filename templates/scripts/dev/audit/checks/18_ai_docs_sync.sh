#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 18_ai_docs_sync.sh — Coherence of AI-context files
# ═══════════════════════════════════════════════════════════════════════════
#
# Verifies:
#   18.1  Each directory in SKILLS_DIR has a SKILL.md whose frontmatter has
#         `name: <dirname>` and a non-empty `description:`.
#   18.2  Each real skill is indexed in AGENTS_MD (AGENTS_INDEX_RE pattern).
#   18.3  Each skill indexed in AGENTS_MD exists on disk (reverse check).
#   18.4  AGENTS_MD stays under the AGENTS_MD_MAX line budget (guardrail).
#
# All paths come from the profile .conf (AGENTS_MD, SKILLS_DIR, ...).
# A kit-style repo may point them at a templates/ subtree; a generated
# project points them at the root (AGENTS.md, .agents/skills).
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "18. AI-context file coherence"

AGENTS_FILE="$PROJECT_ROOT/${AGENTS_MD:-AGENTS.md}"
SKILLS="${SKILLS_DIR:-.agents/skills}"
SKILLS_ABS="$PROJECT_ROOT/$SKILLS"
MAX_LINES="${AGENTS_MD_MAX:-120}"

SKILL_NAMES=()
if [ -d "$SKILLS_ABS" ]; then
    for d in "$SKILLS_ABS"/*/; do
        [ -d "$d" ] || continue
        SKILL_NAMES+=("$(basename "$d")")
    done
fi

# ── 18.1 Frontmatter name/description in each SKILL.md ──
echo "── 18.1 Frontmatter name/description in each SKILL.md ──"
if [ "${#SKILL_NAMES[@]}" -eq 0 ]; then
    log_error "No skills under $SKILLS_ABS"
else
    for name in "${SKILL_NAMES[@]}"; do
        skill_md="$SKILLS_ABS/$name/SKILL.md"
        if [ ! -f "$skill_md" ]; then
            log_error "Skill '$name' has no SKILL.md"
            continue
        fi
        front=$(sed -n '/^---$/,/^---$/p' "$skill_md" | head -20)
        ok=1
        if ! echo "$front" | grep -q "^name: $name$"; then
            log_error "Skill '$name': frontmatter lacks 'name: $name'"
            ok=0
        fi
        if ! echo "$front" | grep -qE '^description: .+'; then
            log_error "Skill '$name': frontmatter lacks a non-empty description"
            ok=0
        fi
        [ "$ok" -eq 1 ] && log_ok "Skill '$name' frontmatter OK"
    done
fi

# ── 18.2 Every real skill indexed in AGENTS.md ──
echo "── 18.2 Skills indexed in ${AGENTS_MD:-AGENTS.md} ──"
if [ ! -f "$AGENTS_FILE" ]; then
    log_error "Missing $AGENTS_FILE"
else
    for name in "${SKILL_NAMES[@]}"; do
        # shellcheck disable=SC2059
        re=$(printf "${AGENTS_INDEX_RE:-\\.agents/skills/%s/SKILL\\.md}" "$name")
        if grep -qE "$re" "$AGENTS_FILE"; then
            log_ok "Skill '$name' indexed in $(basename "$AGENTS_FILE")"
        else
            log_error "Skill '$name' NOT indexed in ${AGENTS_MD:-AGENTS.md}"
        fi
    done
fi

# ── 18.3 Every indexed skill exists on disk (reverse) ──
echo "── 18.3 Indexed skills exist on disk ──"
if [ -f "$AGENTS_FILE" ]; then
    INDEXED=$(grep -oE '\.agents/skills/[a-z0-9_-]+/SKILL\.md' "$AGENTS_FILE" \
        | sed -E 's|\.agents/skills/([a-z0-9_-]+)/SKILL\.md|\1|' | sort -u || true)
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        if [ -f "$SKILLS_ABS/$name/SKILL.md" ]; then
            log_ok "Indexed skill '$name' exists"
        else
            log_error "Indexed skill '$name' has no $SKILLS/$name/SKILL.md"
        fi
    done <<< "$INDEXED"
fi

# ── 18.4 AGENTS.md line budget (anti-regression guardrail) ──
echo "── 18.4 ${AGENTS_MD:-AGENTS.md} size (line budget) ──"
if [ -f "$AGENTS_FILE" ]; then
    AGENTS_LINES=$(wc -l < "$AGENTS_FILE")
    if [ "$AGENTS_LINES" -gt "$MAX_LINES" ]; then
        log_warning "$(basename "$AGENTS_FILE") has $AGENTS_LINES lines (> $MAX_LINES). Trim it or raise the budget deliberately."
    else
        log_ok "$(basename "$AGENTS_FILE") within budget ($AGENTS_LINES ≤ $MAX_LINES lines)"
    fi
fi

audit_exit
