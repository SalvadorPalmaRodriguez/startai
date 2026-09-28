#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# run_all.sh — Unified entry point for repository audits
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   bash run_all.sh --profile <name> [--strict] [--output <path>] [--json <path>]
#
# Flags:
#   --profile <name>       Check profile (profiles/<name>.conf) — required
#   --project-root <path>  Root of the repo to audit (default: repo root)
#   --strict               Warnings also block (exit 2)
#   --output <path>        Full transcript without ANSI to that file
#   --json <path>          JSON report per check + totals
#   --help                 This help
#
# Contract with the checks (lib/common.sh::audit_exit):
#   Each check prints a sentinel line "AUDIT_RESULT check=<name>
#   errors=<N> warnings=<N> infos=<N>" before exiting. run_all.sh uses it as
#   the source of truth for counters, cross-checks the real exit code against
#   the expected one, and compares the declared counters with the actually
#   printed '❌ ERROR:'/'⚠️  WARN:' lines (catches log_error/log_warning lost
#   in pipe subshells).
#
# Exit codes:
#   0 = all OK
#   1 = blocking errors detected (includes infrastructure failures)
#   2 = only warnings (with --strict, also blocks)
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── Defaults ───
PROFILE=""
PROJECT_ROOT=""
STRICT=false
REPORT_PATH=""
JSON_PATH=""

# ─── Parse args ───
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile|--project-root|--output|--json)
            if [[ $# -lt 2 || "$2" == -* ]]; then
                echo "ERROR: $1 requires a value (path/name)"
                exit 1
            fi
            case $1 in
                --profile) PROFILE="$2" ;;
                --project-root) PROJECT_ROOT="$2" ;;
                --output) REPORT_PATH="$2" ;;
                --json) JSON_PATH="$2" ;;
            esac
            shift 2 ;;
        --strict) STRICT=true; shift ;;
        --help|-h)
            sed -n '2,31p' "$0" | grep "^#" | sed 's/^# *//'
            echo ""
            echo "Available profiles:"
            ls "$SCRIPT_DIR/profiles/"*.conf 2>/dev/null | sed 's/.*\//  /;s/\.conf//' | sort
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Validation ───
if [ -z "$PROFILE" ]; then
    echo "ERROR: --profile is required"
    echo "Profiles: $(ls "$SCRIPT_DIR/profiles/"*.conf 2>/dev/null | sed 's/.*\//\n  /;s/\.conf//' | sort)"
    exit 1
fi

PROFILE_FILE="$SCRIPT_DIR/profiles/$PROFILE.conf"
if [ ! -f "$PROFILE_FILE" ]; then
    echo "ERROR: Profile '$PROFILE' not found at $PROFILE_FILE"
    exit 1
fi

if [ -z "$PROJECT_ROOT" ]; then
    # scripts/dev/audit → repo root
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: PROJECT_ROOT does not exist: $PROJECT_ROOT"
    exit 1
fi

# ─── Load profile ───
source "$PROFILE_FILE"

if [ "${#CHECKS[@]}" -eq 0 ]; then
    echo "ERROR: Profile '$PROFILE' defines no checks"
    exit 1
fi

# ─── Colors ───
RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[0;33m'; BLU='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

REPO_NAME="$(basename "$PROJECT_ROOT")"
AUDIT_DATE="$(date '+%Y-%m-%d %H:%M:%S')"

main() {
    # ─── Header ───
    echo -e "\n$BOLD$BLU╔═════════════════════════════════════════════════════════════╗$NC"
    echo -e "$BOLD$BLU║  AUDIT — Unified repository audit                            ║$NC"
    echo -e "$BOLD$BLU║  Perfil: $PROFILE                                             ║$NC"
    PADDING=$((40 - ${#PROFILE} - ${#REPO_NAME}))
    [ "$PADDING" -lt 0 ] && PADDING=0
    echo -e "$BOLD$BLU║  Repo: $REPO_NAME$(printf '%*s' "$PADDING" '')║$NC"
    echo -e "$BOLD$BLU║  Fecha: $AUDIT_DATE                             ║$NC"
    echo -e "$BOLD$BLU║  Checks: ${#CHECKS[@]}                                              ║$NC"
    echo -e "$BOLD$BLU║  Strict: $STRICT                                               ║$NC"
    echo -e "$BOLD$BLU╚═════════════════════════════════════════════════════════════╝$NC\n"

    # ─── Run checks ───
    TOTAL_ERRORS=0
    TOTAL_WARNINGS=0
    TOTAL_INFOS=0
    FAILED_CHECKS=()
    CHECK_RESULTS=()

    for check in "${CHECKS[@]}"; do
        check_script="$SCRIPT_DIR/checks/$check.sh"
        if [ ! -x "$check_script" ]; then
            echo -e "$RED❌ Check not found or not executable: $check.sh$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (missing)")
            CHECK_RESULTS+=("$check|-1|0|0|0|infra")
            continue
        fi

        echo -e "$BOLD$BLU▶ $check$NC"

        # Run the check with inherited environment — keep the real exit code.
        # Checks re-source the profile file themselves (arrays cannot be
        # exported to child processes), via PROFILE + PROFILE_FILE.
        OUTPUT=$(PROJECT_ROOT="$PROJECT_ROOT" PROFILE="$PROFILE" STRICT="$STRICT" \
            PROFILE_FILE="$PROFILE_FILE" bash "$check_script" 2>&1)
        rc=$?
        echo "$OUTPUT"

        CLEAN=$(printf '%s\n' "$OUTPUT" | sed 's/\x1b\[[0-9;]*m//g')
        SENTINEL=$(printf '%s\n' "$CLEAN" | grep '^AUDIT_RESULT ' | tail -1)

        if [ -z "$SENTINEL" ]; then
            echo -e "$RED❌ ERROR: Check '$check' did not emit AUDIT_RESULT (rc=$rc) — possible abort or syntax error$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (no AUDIT_RESULT)")
            CHECK_RESULTS+=("$check|$rc|0|0|0|infra")
            echo ""
            continue
        fi

        cerr=$(printf '%s\n' "$SENTINEL" | sed -n 's/.*errors=\([^ ]*\).*/\1/p')
        cwarn=$(printf '%s\n' "$SENTINEL" | sed -n 's/.*warnings=\([^ ]*\).*/\1/p')
        cinfo=$(printf '%s\n' "$SENTINEL" | sed -n 's/.*infos=\([^ ]*\).*/\1/p')

        if ! [[ "$cerr" =~ ^[0-9]+$ && "$cwarn" =~ ^[0-9]+$ && "$cinfo" =~ ^[0-9]+$ ]]; then
            echo -e "$RED❌ ERROR: unreadable AUDIT_RESULT in '$check'$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (unreadable AUDIT_RESULT)")
            CHECK_RESULTS+=("$check|$rc|0|0|0|infra")
            echo ""
            continue
        fi

        status="ok"
        [ "$cwarn" -gt 0 ] && status="warnings"
        [ "$cerr" -gt 0 ] && status="errors"
        infra_fail=false

        # expected rc: 1 if errors>0; 2 if errors==0 && warnings>0 && strict; 0 else
        exp=0
        if [ "$cerr" -gt 0 ]; then
            exp=1
        elif [ "$STRICT" = true ] && [ "$cwarn" -gt 0 ]; then
            exp=2
        fi
        if [ "$rc" -ne "$exp" ]; then
            echo -e "$RED❌ ERROR: incoherent rc in '$check': rc=$rc, expected=$exp (errors=$cerr warnings=$cwarn strict=$STRICT)$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (incoherent rc)")
            infra_fail=true
        fi

        # Declared-vs-printed contrast (catches counters lost in subshells)
        perr=$(printf '%s\n' "$CLEAN" | grep -c '❌ ERROR:')
        pwarn=$(printf '%s\n' "$CLEAN" | grep -c '⚠️  WARN:')
        if [ "$perr" -gt "$cerr" ]; then
            echo -e "$RED❌ ERROR: inconsistent counter in '$check': $perr '❌ ERROR:' lines printed vs $cerr declared (log_error inside a subshell?)$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (inconsistent counter)")
            infra_fail=true
        fi
        if [ "$pwarn" -gt "$cwarn" ]; then
            echo -e "$RED❌ ERROR: inconsistent counter in '$check': $pwarn '⚠️  WARN:' lines printed vs $cwarn declared (log_warning inside a subshell?)$NC"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            FAILED_CHECKS+=("$check (inconsistent counter)")
            infra_fail=true
        fi

        [ "$infra_fail" = true ] && status="infra"

        TOTAL_ERRORS=$((TOTAL_ERRORS + cerr))
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + cwarn))
        TOTAL_INFOS=$((TOTAL_INFOS + cinfo))
        CHECK_RESULTS+=("$check|$rc|$cerr|$cwarn|$cinfo|$status")

        echo ""
    done

    # ─── Global exit code ───
    EXIT_CODE=0
    if [ "$TOTAL_ERRORS" -gt 0 ]; then
        EXIT_CODE=1
    elif [ "$STRICT" = true ] && [ "$TOTAL_WARNINGS" -gt 0 ]; then
        EXIT_CODE=2
    fi

    # ─── JSON report ───
    if [ -n "$JSON_PATH" ]; then
        mkdir -p "$(dirname "$JSON_PATH")" 2>/dev/null || true
        RESULTS_FILE=$(mktemp)
        printf '%s\n' "${CHECK_RESULTS[@]}" > "$RESULTS_FILE"
        PROFILE="$PROFILE" REPO_NAME="$REPO_NAME" AUDIT_DATE="$AUDIT_DATE" \
        STRICT="$STRICT" JSON_PATH="$JSON_PATH" EXIT_CODE="$EXIT_CODE" \
        TOTAL_ERRORS="$TOTAL_ERRORS" TOTAL_WARNINGS="$TOTAL_WARNINGS" TOTAL_INFOS="$TOTAL_INFOS" \
        python3 - "$RESULTS_FILE" <<'PYEOF'
import json, os, sys

checks = []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.rstrip("\n")
    if not line:
        continue
    name, rc, e, w, i, st = line.split("|")
    checks.append({"check": name, "rc": int(rc), "errors": int(e),
                   "warnings": int(w), "infos": int(i), "status": st})

data = {
    "profile": os.environ["PROFILE"],
    "repo": os.environ["REPO_NAME"],
    "date": os.environ["AUDIT_DATE"],
    "strict": os.environ["STRICT"] == "true",
    "checks": checks,
    "totals": {"errors": int(os.environ["TOTAL_ERRORS"]),
               "warnings": int(os.environ["TOTAL_WARNINGS"]),
               "infos": int(os.environ["TOTAL_INFOS"])},
    "exit": int(os.environ["EXIT_CODE"]),
}
with open(os.environ["JSON_PATH"], "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
        rm -f "$RESULTS_FILE"
    fi

    # ─── Summary ───
    echo -e "$BOLD$BLU═══════════════════════════════════════════════════════════════$NC"
    echo -e "$BOLD$BLU  FINAL SUMMARY$NC"
    echo -e "$BOLD$BLU═══════════════════════════════════════════════════════════════$NC"
    echo -e "  Profile: $BOLD$PROFILE$NC"
    echo -e "  Repo: $BOLD$REPO_NAME$NC"
    echo -e "  Checks run: $BOLD${#CHECKS[@]}$NC"
    echo -e "  Errors: $RED$BOLD$TOTAL_ERRORS$NC"
    echo -e "  Warnings: $YEL$BOLD$TOTAL_WARNINGS$NC"

    if [ "${#FAILED_CHECKS[@]}" -gt 0 ]; then
        printf '  %sChecks with infrastructure failure:%s
' "$RED" "$NC"
        printf '    - %s\n' "${FAILED_CHECKS[@]}"
    fi

    if [ "$TOTAL_ERRORS" -gt 0 ]; then
        echo -e "\n  $RED$BOLD❌ AUDIT BLOCKED — $TOTAL_ERRORS errors$NC"
        echo -e "  $BOLD$BLU═══════════════════════════════════════════════════════════════$NC\n"
        exit "$EXIT_CODE"
    fi

    if [ "$STRICT" = true ] && [ "$TOTAL_WARNINGS" -gt 0 ]; then
        echo -e "\n  $YEL$BOLD⚠️  AUDIT BLOCKED (strict) — $TOTAL_WARNINGS warnings$NC"
        echo -e "  $BOLD$BLU═══════════════════════════════════════════════════════════════$NC\n"
        exit "$EXIT_CODE"
    fi

    if [ "$TOTAL_WARNINGS" -gt 0 ]; then
        echo -e "\n  $YEL$BOLD⚠️  AUDIT OK with $TOTAL_WARNINGS warnings$NC"
    else
        echo -e "\n  $GRN$BOLD✅ CLEAN AUDIT — 0 errors, 0 warnings$NC"
    fi
    echo -e "  $BOLD$BLU═══════════════════════════════════════════════════════════════$NC\n"
    exit "$EXIT_CODE"
}

# ─── Optional transcript (--output) ───
if [ -n "$REPORT_PATH" ]; then
    mkdir -p "$(dirname "$REPORT_PATH")" 2>/dev/null || true
    REPORT_TMP=$(mktemp)
    main | tee "$REPORT_TMP"
    rc="${PIPESTATUS[0]}"
    sed 's/\x1b\[[0-9;]*m//g' "$REPORT_TMP" > "$REPORT_PATH"
    rm -f "$REPORT_TMP"
    exit "$rc"
fi

main
