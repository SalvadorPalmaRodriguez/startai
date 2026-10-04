#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# 01_secrets_and_creds.sh — Real credentials in code and docs
# ═══════════════════════════════════════════════════════════════════════════
#
# Verifies that no passwords, API keys, tokens, private keys or connection
# strings are hardcoded in the published surface of the repo.
#
# Whitelist (does not block):
#   - Environment variables: $MY_PASS, $SOME_TOKEN
#   - Placeholders: <password>, 'your-password', test1234, "changeme"
#   - Template tokens of the scaffold engine (contain a '{' before the value)
#   - Test/fixture/example paths
#
# Scope: SECRET_SCAN_DIRS + SECRET_SCAN_FILES from the profile .conf.
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
ERRORS=0; WARNINGS=0; INFOS=0; STRICT="${STRICT:-false}"
audit_source_profile || true

log_section "01. Hardcoded secrets and credentials"

# ── Build the scan target list from the profile ──
SCAN_TARGETS=()
for d in "${SECRET_SCAN_DIRS[@]:-}"; do
    [ -d "$PROJECT_ROOT/$d" ] && SCAN_TARGETS+=("$PROJECT_ROOT/$d")
done
for f in "${SECRET_SCAN_FILES[@]:-}"; do
    [ -f "$PROJECT_ROOT/$f" ] && SCAN_TARGETS+=("$PROJECT_ROOT/$f")
done

if [ "${#SCAN_TARGETS[@]}" -eq 0 ]; then
    log_warning "No scan targets found (profile SECRET_SCAN_*)"
    audit_exit
fi

INCLUDES=(
    --include='*.md'  --include='*.sh'   --include='*.py'
    --include='*.json' --include='*.toml' --include='*.yml'
    --include='*.yaml' --include='*.html' --include='*.txt'
    --include='*.conf'
)

# Shared exclusion filter: tests, fixtures, placeholders, comments.
EXCLUDE_RE='tests::|/tests/|test_|_test\.|fixtures|mock|example|placeholder|//|test1234'

# ── 1.1 Private keys (PEM/DER) ──
echo "── 1.1 Private keys (PEM/DER) ──"
PRIVATE_KEYS=$(grep -rnE -- '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" || true)
if [ -n "$PRIVATE_KEYS" ]; then
    COUNT=$(echo "$PRIVATE_KEYS" | wc -l | tr -d ' ')
    log_error "Private keys found: $COUNT"
    echo "$PRIVATE_KEYS" | head -5 | sed 's/^/    /'
else
    log_ok "No private keys in code/docs"
fi

# ── 1.2 API keys (sk-, gsk_, xai-, ghp_, gho_, ghs_) ──
echo "── 1.2 API keys (sk-/gsk_/xai-/ghp_/gho_/ghs_) ──"
API_KEYS=$(grep -rnE '(sk-[a-zA-Z0-9]{30,}|gsk_[a-zA-Z0-9]{30,}|xai-[a-zA-Z0-9]{30,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|ghs_[a-zA-Z0-9]{36})' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" || true)
if [ -n "$API_KEYS" ]; then
    COUNT=$(echo "$API_KEYS" | wc -l | tr -d ' ')
    log_error "Suspicious API keys: $COUNT"
    echo "$API_KEYS" | head -5 | sed 's/^/    /'
else
    log_ok "No hardcoded API keys"
fi

# ── 1.3 Complete JWT tokens (eyJ... >100 chars) ──
echo "── 1.3 Complete JWT tokens ──"
JWT_TOKENS=$(grep -rnE 'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" || true)
if [ -n "$JWT_TOKENS" ]; then
    COUNT=$(echo "$JWT_TOKENS" | wc -l | tr -d ' ')
    log_error "Complete JWT tokens found: $COUNT"
    echo "$JWT_TOKENS" | head -3 | sed 's/^/    /'
else
    log_ok "No hardcoded JWT tokens"
fi

# ── 1.4 Bearer tokens ──
echo "── 1.4 Bearer tokens ──"
BEARER_TOKENS=$(grep -rnE 'Bearer [a-zA-Z0-9_-]{40,}' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" || true)
if [ -n "$BEARER_TOKENS" ]; then
    COUNT=$(echo "$BEARER_TOKENS" | wc -l | tr -d ' ')
    log_error "Bearer tokens found: $COUNT"
    echo "$BEARER_TOKENS" | head -3 | sed 's/^/    /'
else
    log_ok "No hardcoded Bearer tokens"
fi

# ── 1.5 Connection strings with credentials ──
echo "── 1.5 Connection strings with credentials ──"
CONN_STRINGS=$(grep -rnE '(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" | grep -vE 'user:pass|user:password' || true)
if [ -n "$CONN_STRINGS" ]; then
    COUNT=$(echo "$CONN_STRINGS" | wc -l | tr -d ' ')
    log_error "Connection strings with credentials: $COUNT"
    echo "$CONN_STRINGS" | head -3 | sed 's/^/    /'
else
    log_ok "No connection strings with credentials"
fi

# ── 1.6 Hardcoded passwords (assignment with real value) ──
echo "── 1.6 Hardcoded passwords (assignment with real value) ──"
HARDCODED_PASS=$(grep -rnE '(password|passwd|pass|api_key|apikey|secret|token)\s*[=:]\s*["'\''][^$<{"'\'']{4,}["'\'']' \
    "${SCAN_TARGETS[@]}" \
    --include='*.py' --include='*.sh' --include='*.toml' \
    --include='*.json' --include='*.yml' --include='*.yaml' \
    2>/dev/null \
    | grep -vE "$EXCLUDE_RE" \
    | grep -vE 'changeme|your-password|<password>|_ENV|_FILE|dummy|fake|sample|redacted' \
    || true)
if [ -n "$HARDCODED_PASS" ]; then
    COUNT=$(echo "$HARDCODED_PASS" | wc -l | tr -d ' ')
    log_error "Suspicious hardcoded passwords/keys: $COUNT"
    echo "$HARDCODED_PASS" | head -5 | sed 's/^/    /'
else
    log_ok "No hardcoded passwords in code"
fi

# ── 1.7 AWS / GCP credentials ──
echo "── 1.7 AWS/GCP credentials ──"
AWS_KEYS=$(grep -rnE '(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})' \
    "${SCAN_TARGETS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" || true)
if [ -n "$AWS_KEYS" ]; then
    COUNT=$(echo "$AWS_KEYS" | wc -l | tr -d ' ')
    log_error "AWS/GCP keys found: $COUNT"
    echo "$AWS_KEYS" | head -3 | sed 's/^/    /'
else
    log_ok "No AWS/GCP credentials"
fi

audit_exit
