#!/usr/bin/env bash
# sync_version.sh — Propagate the canonical product version to its consumers.
#
# Canonical source: CHANGELOG.md → first '## [x.y.z]' heading (Keep a
# Changelog format; an '[Unreleased]' heading is skipped automatically).
#
# Usage:
#   bash scripts/dev/sync_version.sh                 # propagate (sync mode)
#   bash scripts/dev/sync_version.sh --check         # verify only, exit 0/1
#   bash scripts/dev/sync_version.sh --bump X.Y.Z    # release X.Y.Z: turn the
#                                                    #   [Unreleased] entry into
#                                                    #   '[X.Y.Z] - <today>' plus a
#                                                    #   fresh empty [Unreleased],
#                                                    #   then propagate
#   bash scripts/dev/sync_version.sh --release-feed  # feed/: set 'latest' +
#                                                    #   'published_at' (ISO UTC)
#                                                    #   and re-sign with
#                                                    #   feed/minisign.key
#
# Propagation targets (allowlist of "path:kind" entries, kind ∈ json_version |
# badge_version | current_version) are read from VERSION_TARGETS in the audit
# profile (scripts/dev/audit/profiles/*.conf) — the very same list that check
# 19_version_sync verifies. DEFAULT_TARGETS below is only a fallback for repos
# without an audit profile. If you change one, change the other.
#
# NEVER targets:
#   - CHANGELOG.md itself (it IS the canonical source).
#   - 'Versión:'/'Version:' headers in docs/ or AGENTS.md — those are
#     DOCUMENT versions, unrelated to the product version.
#   - feed/advisories.json 'published_at' and its signature — only
#     --release-feed touches them (the feed is minisign-signed).
#
# This file is shipped verbatim to generated projects — keep it generic.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

CHANGELOG="CHANGELOG.md"
FEED_JSON="feed/advisories.json"
FEED_SIG="feed/advisories.json.minisig"
FEED_KEY="${FEED_MINISIGN_KEY:-feed/minisign.key}"
FEED_PUB="feed/minisign.pub"

# Fallback allowlist when no audit profile exists (mirrors the standard
# generated project: config.json "version" key, README version badges,
# llms-full.txt "Current version:" line).
DEFAULT_TARGETS=(
    "config.json:json_version"
    "README.md:badge_version"
    "README.es.md:badge_version"
    "llms-full.txt:current_version"
)

log()  { printf '\n── %s ──\n' "$*"; }
ok()   { echo "  ✅ $*"; }
warn() { echo "  ⚠️  $*"; }
info() { echo "  ℹ️  $*"; }
err()  { echo "  ❌ $*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
    sed -n '2,32p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 0
}

# ─── Args ────────────────────────────────────────────────────────────────────
MODE="sync"
NEW_VERSION=""
EXPECT_BUMP=0
for arg in "$@"; do
    case "$arg" in
        --check)        MODE="check" ;;
        --bump)         MODE="bump"; EXPECT_BUMP=1 ;;
        --release-feed) MODE="release-feed" ;;
        --help|-h)      usage ;;
        *) if [ "$EXPECT_BUMP" = "1" ]; then
               NEW_VERSION="$arg"; EXPECT_BUMP=0
           else
               die "Unknown argument: $arg (try --help)"
           fi ;;
    esac
done

# ─── Canonical version ───────────────────────────────────────────────────────
get_canonical() {
    [ -f "$CHANGELOG" ] || return 1
    grep -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+[^]]*\]' "$CHANGELOG" \
        | head -1 | sed -E 's/^## \[([^]]+)\]/\1/'
}

# ─── Load the target allowlist from the audit profile ────────────────────────
TARGETS=()
PROFILE_CONF=$(ls scripts/dev/audit/profiles/*.conf 2>/dev/null | head -1 || true)
if [ -n "$PROFILE_CONF" ]; then
    # shellcheck disable=SC1090
    . "$PROFILE_CONF"
    if declare -p VERSION_TARGETS 2>/dev/null | grep -q '^declare'; then
        if [ "${#VERSION_TARGETS[@]}" -gt 0 ]; then
            TARGETS=("${VERSION_TARGETS[@]}")
        fi
    else
        TARGETS=("${DEFAULT_TARGETS[@]}")
    fi
else
    TARGETS=("${DEFAULT_TARGETS[@]}")
fi

# ─── Bump: rewrite the CHANGELOG first ───────────────────────────────────────
if [ "$MODE" = "bump" ]; then
    [ -n "$NEW_VERSION" ] \
        || die "--bump requires a version: bash scripts/dev/sync_version.sh --bump X.Y.Z"
    echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' \
        || die "Invalid version '$NEW_VERSION' (expected X.Y.Z[-prerelease])"
    [ -f "$CHANGELOG" ] || die "$CHANGELOG not found"

    TODAY=$(date -u +%Y-%m-%d)
    if grep -qE '^## \[Unreleased\]' "$CHANGELOG"; then
        # Rename [Unreleased] to the dated release and open a fresh empty
        # [Unreleased] above it (any bullets under it become the release notes).
        sed -i -E "0,/^## \[Unreleased\].*/s/^## \[Unreleased\].*/## [Unreleased]\n\n## [$NEW_VERSION] - $TODAY/" "$CHANGELOG"
    elif grep -qE '^## \[' "$CHANGELOG"; then
        # No [Unreleased] section: insert the new entry before the first release.
        sed -i -E "0,/^## \[/s/^## \[/## [$NEW_VERSION] - $TODAY\n\n## [/" "$CHANGELOG"
    else
        die "$CHANGELOG has no '## [x.y.z]' section to release"
    fi
    ok "$CHANGELOG → new entry [$NEW_VERSION] - $TODAY"
fi

VERSION=$(get_canonical || true)
[ -n "$VERSION" ] || die "No '## [x.y.z]' entry in $CHANGELOG — no canonical version"

# ─── Target kinds ────────────────────────────────────────────────────────────
apply_target() {
    local spec="$1" file kind
    file="${spec%%:*}"; kind="${spec#*:}"
    if [ ! -f "$file" ]; then
        info "$file — not present, skipped"
        return 0
    fi
    case "$kind" in
        json_version)
            sed -i -E "0,/\"version\"[[:space:]]*:[[:space:]]*\"[^\"]+\"/s/\"version\"[[:space:]]*:[[:space:]]*\"[^\"]+\"/\"version\": \"$VERSION\"/" "$file" ;;
        badge_version)
            sed -i -E "s/version-[0-9]+\.[0-9]+\.[0-9]+/version-$VERSION/g" "$file" ;;
        current_version)
            sed -i -E "s/Current version: [0-9]+\.[0-9]+\.[0-9]+/Current version: $VERSION/g" "$file" ;;
        *)
            warn "$file — unknown kind '$kind', skipped"; return 0 ;;
    esac
    ok "$file → $VERSION"
}

check_target() {
    local spec="$1" file kind val other
    file="${spec%%:*}"; kind="${spec#*:}"
    if [ ! -f "$file" ]; then
        info "$file — not present, skipped"
        return 0
    fi
    case "$kind" in
        json_version)
            val=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' "$file" \
                | head -1 | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)"/\1/')
            if [ -z "$val" ]; then
                warn "$file — no \"version\" key"
            elif [ "$val" != "$VERSION" ]; then
                err "$file — version $val != canonical $VERSION"; return 1
            else
                ok "$file — $val"
            fi ;;
        badge_version)
            if grep -qE "version-$VERSION([^0-9]|$)" "$file"; then
                ok "$file — badge version-$VERSION"
            else
                other=$(grep -oE 'version-[0-9]+\.[0-9]+\.[0-9]+' "$file" | head -1 || true)
                if [ -n "$other" ]; then
                    err "$file — badge '$other' != version-$VERSION"; return 1
                fi
                warn "$file — no version badge found"
            fi ;;
        current_version)
            if grep -qE "Current version: $VERSION([^0-9]|$)" "$file"; then
                ok "$file — 'Current version: $VERSION'"
            else
                other=$(grep -oE 'Current version: [0-9]+\.[0-9]+\.[0-9]+' "$file" | head -1 || true)
                if [ -n "$other" ]; then
                    err "$file — '$other' != Current version: $VERSION"; return 1
                fi
                warn "$file — no 'Current version:' line"
            fi ;;
        *)
            warn "$file — unknown kind '$kind', skipped" ;;
    esac
    return 0
}

# ─── Feed (signed — signature handled separately) ───────────────────────────
# sync/check: only the 'latest' field is a version target ('min_supported'
# follows while it was tracking the previous 'latest'; a pinned lower floor is
# respected). 'published_at' and the .minisig are only touched by --release-feed.
feed_json_field() {
    # feed_json_field <key> → prints first "key": "value" pair's value
    grep -oE "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$FEED_JSON" \
        | head -1 | sed -E 's/.*"([^"]*)"$/\1/'
}

sync_feed_latest() {
    [ -f "$FEED_JSON" ] || return 0
    local old_latest cur_min
    old_latest=$(feed_json_field latest)
    cur_min=$(feed_json_field min_supported)
    sed -i -E "s/\"latest\": \"[^\"]*\"/\"latest\": \"$VERSION\"/" "$FEED_JSON"
    if [ -n "$cur_min" ] && [ "$cur_min" = "$old_latest" ]; then
        # min_supported was tracking latest → keep tracking.
        sed -i -E "s/\"min_supported\": \"[^\"]*\"/\"min_supported\": \"$VERSION\"/" "$FEED_JSON"
    fi
    ok "$FEED_JSON → latest=$VERSION (min_supported=${cur_min:-none}→$(feed_json_field min_supported))"
    [ -f "$FEED_KEY" ] || warn "$FEED_JSON updated — its .minisig is stale until --release-feed re-signs (no $FEED_KEY)"
}

check_feed_latest() {
    [ -f "$FEED_JSON" ] || { info "$FEED_JSON — not present, skipped"; return 0; }
    local cur
    cur=$(feed_json_field latest)
    if [ "$cur" != "$VERSION" ]; then
        err "$FEED_JSON — latest=$cur != canonical $VERSION"
        return 1
    fi
    ok "$FEED_JSON — latest=$cur"
    return 0
}

release_feed() {
    if [ ! -f "$FEED_JSON" ]; then
        warn "$FEED_JSON not found — this project does not ship a signed update feed; nothing to do."
        return 0
    fi
    local now
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    sync_feed_latest
    sed -i -E "s/\"published_at\": \"[^\"]*\"/\"published_at\": \"$now\"/" "$FEED_JSON"
    ok "$FEED_JSON → published_at=$now"
    if [ -f "$FEED_KEY" ]; then
        command -v minisign >/dev/null 2>&1 \
            || { warn "minisign not in PATH — feed updated but NOT signed"; return 0; }
        minisign -S -s "$FEED_KEY" -m "$FEED_JSON" -x "$FEED_SIG"
        ok "feed re-signed → $FEED_SIG"
        if [ -f "$FEED_PUB" ]; then
            if minisign -V -m "$FEED_JSON" -x "$FEED_SIG" -p "$FEED_PUB" >/dev/null 2>&1; then
                ok "feed signature verified with $FEED_PUB"
            else
                warn "feed signature verification FAILED against $FEED_PUB"
            fi
        fi
    else
        warn "$FEED_KEY not found — feed updated but NOT signed (unsigned feed; see feed/README.md)"
    fi
}

# ─── Dispatch ────────────────────────────────────────────────────────────────
case "$MODE" in
    release-feed)
        release_feed
        exit 0 ;;

    check)
        drift=0
        if [ "${#TARGETS[@]}" -eq 0 ]; then
            info "no VERSION_TARGETS configured (profile: ${PROFILE_CONF:-none}) — only the canonical version is verified"
        fi
        for spec in ${TARGETS[@]+"${TARGETS[@]}"}; do
            check_target "$spec" || drift=1
        done
        check_feed_latest || drift=1
        if [ "$drift" -ne 0 ]; then
            echo ""
            err "Version drift detected — run: bash scripts/dev/sync_version.sh"
            exit 1
        fi
        echo ""
        echo "✅ Version $VERSION coherent across all targets."
        exit 0 ;;

    sync|bump)
        for spec in ${TARGETS[@]+"${TARGETS[@]}"}; do
            apply_target "$spec"
        done
        sync_feed_latest
        echo ""
        echo "✅ Version $VERSION propagated."
        [ "$MODE" = "bump" ] && echo "   (feed published_at/signature: refresh with --release-feed during the release)"
        exit 0 ;;
esac
