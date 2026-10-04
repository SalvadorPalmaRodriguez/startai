#!/usr/bin/env bash
# release.sh — Release pipeline: audit → version → feed → tag → package →
# GitHub release.
#
# Usage:
#   bash scripts/dev/release.sh                 # release the CHANGELOG version
#   bash scripts/dev/release.sh --bump X.Y.Z    # bump first, then release
#   bash scripts/dev/release.sh --dry-run       # print the plan, run nothing
#   bash scripts/dev/release.sh --yes           # skip the publish confirmation
#   bash scripts/dev/release.sh --allow-unsigned # publish without signatures
#                                               # (explicit opt-out)
#
# Requirements (non --dry-run):
#   - git repository on main|master with a clean worktree
#   - gh CLI authenticated (gh auth status)
#   - minisign in PATH + a signing key — unsigned output aborts the release
#     unless --allow-unsigned is passed explicitly
#   - python3 (config.json parsing)
#
# Pipeline:
#   0. Preconditions          4. Commit release changes (signed if PGP works)
#   1. Audit --strict          5. Tag v<X.Y.Z> (git tag -s, fallback -a)
#   2. sync_version.sh         6. Package git archive → dist/ + sha256 + minisign
#      (--check or --bump)     7. Push + gh release create (notes = CHANGELOG
#   3. sync_version.sh             section of this version)
#      --release-feed          8. Summary
#
# This file is shipped verbatim to generated projects — keep it generic.
# Identity: REPO_NAME/GH_REPO are derived from config.json (keys "repo" and
# "github_user") when it exists, else from `git remote get-url origin`, else
# from the directory name. Projects that compile artifacts hook a build in via
#   BUILD_CMD="make release" bash scripts/dev/release.sh
# Post-quantum (ML-DSA-65) artifact signing is documented in
# .agents/skills/signing/SKILL.md — a manual ceremony layered on top of the
# minisign signatures produced here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

CHANGELOG="CHANGELOG.md"
SYNC_SH="scripts/dev/sync_version.sh"
MINISIGN_KEY="${RELEASE_MINISIGN_KEY:-}"

log()  { printf '\n\033[1;36m═══ %s ═══\033[0m\n' "$*"; }
ok()   { printf '  \033[1;32m✅\033[0m %s\n' "$*"; }
warn() { printf '  \033[1;33m⚠️\033[0m  %s\n' "$*"; }
die()  { printf '  \033[1;31m❌\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    sed -n '2,35p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 0
}

# ─── Args ────────────────────────────────────────────────────────────────────
DRY_RUN=0
BUMP=""
YES=0
ALLOW_UNSIGNED=0
EXPECT_BUMP=0
for arg in "$@"; do
    case "$arg" in
        --dry-run)   DRY_RUN=1 ;;
        --bump)      EXPECT_BUMP=1 ;;
        --yes|-y)    YES=1 ;;
        --allow-unsigned) ALLOW_UNSIGNED=1 ;;
        --help|-h)   usage ;;
        *) if [ "$EXPECT_BUMP" = "1" ]; then
               BUMP="$arg"; EXPECT_BUMP=0
           else
               die "Unknown argument: $arg (try --help)"
           fi ;;
    esac
done
[ "$EXPECT_BUMP" = "0" ] || die "--bump requires a version: --bump X.Y.Z"

# ─── Helpers ─────────────────────────────────────────────────────────────────
canon_version() {
    [ -f "$CHANGELOG" ] || return 1
    grep -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+[^]]*\]' "$CHANGELOG" \
        | head -1 | sed -E 's/^## \[([^]]+)\]/\1/'
}

json_get() {
    # json_get <key> <file> → value or empty (never fails)
    python3 - "$1" "$2" <<'PY' 2>/dev/null || true
import json, sys
try:
    print(json.load(open(sys.argv[2])).get(sys.argv[1], ""))
except Exception:
    pass
PY
}

# ─── Identity (config.json > git remote > dirname) ───────────────────────────
REPO_NAME=""
PRODUCT_NAME=""
GH_REPO=""
if [ -f config.json ]; then
    cfg_user=$(json_get github_user config.json)
    cfg_repo=$(json_get repo config.json)
    cfg_name=$(json_get product_name config.json)
    [ -n "$cfg_repo" ] && REPO_NAME="$cfg_repo"
    [ -n "$cfg_name" ] && PRODUCT_NAME="$cfg_name"
    [ -n "$cfg_user" ] && [ -n "$cfg_repo" ] && GH_REPO="$cfg_user/$cfg_repo"
fi
if [ -z "$GH_REPO" ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    remote=$(git remote get-url origin 2>/dev/null || true)
    if [ -n "$remote" ]; then
        parsed=$(printf '%s' "$remote" | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')
        [ "$parsed" != "$remote" ] && GH_REPO="$parsed"
    fi
fi
[ -z "$REPO_NAME" ] && REPO_NAME="${GH_REPO##*/}"
[ -z "$REPO_NAME" ] && REPO_NAME=$(basename "$PROJECT_ROOT")
[ -z "$PRODUCT_NAME" ] && PRODUCT_NAME="$REPO_NAME"

VERSION=$(canon_version || true)
TAG="v${VERSION:-?}"

# Audit profile: the single conf shipped in this repo (profiles/*.conf).
AUDIT_PROFILE=""
conf=$(ls scripts/dev/audit/profiles/*.conf 2>/dev/null | head -1 || true)
[ -n "$conf" ] && AUDIT_PROFILE=$(basename "$conf" .conf)

# Minisign key for artifacts: env override → feed key → repo-root key →
# per-product key (~/.minisign/<repo>.key).
[ -z "$MINISIGN_KEY" ] && [ -f feed/minisign.key ] && MINISIGN_KEY="feed/minisign.key"
[ -z "$MINISIGN_KEY" ] && [ -f minisign.key ] && MINISIGN_KEY="minisign.key"
[ -z "$MINISIGN_KEY" ] && [ -f "$HOME/.minisign/$REPO_NAME.key" ] \
    && MINISIGN_KEY="$HOME/.minisign/$REPO_NAME.key"

# ─── --dry-run: print the plan, run nothing ─────────────────────────────────
if [ "$DRY_RUN" = "1" ]; then
    echo "═══ release.sh — DRY RUN (no changes) ═══"
    echo ""
    echo "  Product : $PRODUCT_NAME"
    echo "  Repo    : ${GH_REPO:-<unknown — set config.json github_user/repo or git remote origin>}"
    echo "  Version : ${VERSION:-<none — CHANGELOG.md has no '## [x.y.z]'>}"
    echo "  Tag     : $TAG"
    echo ""
    echo "Plan:"
    echo "  0. Preconditions: git repo, branch main|master, clean worktree,"
    echo "     gh auth status, minisign in PATH, python3."
    if [ -n "$AUDIT_PROFILE" ]; then
        echo "  1. Audit: bash scripts/dev/audit/run_all.sh --profile $AUDIT_PROFILE --strict"
    else
        echo "  1. Audit: (no scripts/dev/audit profile found — skipped with warning)"
    fi
    if [ -n "$BUMP" ]; then
        echo "  2. Version: bash $SYNC_SH --bump $BUMP  (CHANGELOG entry + propagate)"
    else
        echo "  2. Version: bash $SYNC_SH --check  (abort on drift)"
    fi
    echo "  3. Feed: bash $SYNC_SH --release-feed  (latest + published_at + re-sign if feed/minisign.key)"
    echo "  4. Optional build: BUILD_CMD=${BUILD_CMD:-<none>}"
    echo "  5. Commit release changes (git commit -S, fallback unsigned + warn)"
    echo "  6. Tag: git tag -s $TAG  (fallback: git tag -a + warn)"
    echo "  7. Package: git archive → dist/$REPO_NAME-$TAG.tar.gz + .sha256 + .minisig (aborts without a key unless --allow-unsigned)"
    echo "  8. Push branch + tag; gh release create $TAG <artifacts> --notes-file <CHANGELOG section>"
    echo "  9. Summary"
    echo ""
    echo "Precondition status:"
    check() { if "$@" >/dev/null 2>&1; then echo "  ✅ $*"; else echo "  ❌ $*"; fi; }
    check git rev-parse --is-inside-work-tree
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        b=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        case "$b" in main|master) echo "  ✅ on branch $b" ;; *) echo "  ❌ on branch $b (need main|master)" ;; esac
        if [ -z "$(git status --porcelain 2>/dev/null)" ]; then echo "  ✅ clean worktree"; else echo "  ❌ dirty worktree"; fi
    fi
    check command -v gh
    check gh auth status
    check command -v minisign
    [ -n "$MINISIGN_KEY" ] && echo "  ✅ signing key: $MINISIGN_KEY" \
        || echo "  ❌ no signing key (RELEASE_MINISIGN_KEY / feed/minisign.key / minisign.key / ~/.minisign/$REPO_NAME.key)"
    check command -v python3
    [ -f "$SYNC_SH" ] && echo "  ✅ $SYNC_SH present" || echo "  ❌ $SYNC_SH missing"
    exit 0
fi

# ─── 0. Preconditions ───────────────────────────────────────────────────────
log "0. Preconditions"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "Not a git repository — release.sh must run inside a git worktree"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
case "$BRANCH" in
    main|master) : ;;
    *) die "Not on the main branch (current: $BRANCH)" ;;
esac
[ -z "$(git status --porcelain)" ] \
    || die "Dirty worktree — commit or stash before releasing"
command -v git      >/dev/null || die "git not in PATH"
command -v gh       >/dev/null || die "gh CLI not in PATH"
gh auth status >/dev/null 2>&1 || die "gh CLI not authenticated (gh auth login)"
command -v python3  >/dev/null || die "python3 not in PATH (needed to read config.json)"
command -v sha256sum >/dev/null || die "sha256sum not in PATH"
if [ "$ALLOW_UNSIGNED" = "1" ]; then
    command -v minisign >/dev/null \
        || warn "minisign not in PATH — artifacts unsigned (--allow-unsigned)"
    [ -n "$MINISIGN_KEY" ] \
        || warn "No minisign key — artifacts unsigned (--allow-unsigned)"
else
    command -v minisign >/dev/null \
        || die "minisign not in PATH — install it or pass --allow-unsigned"
    [ -n "$MINISIGN_KEY" ] \
        || die "No minisign key (env RELEASE_MINISIGN_KEY, feed/minisign.key, minisign.key or ~/.minisign/$REPO_NAME.key) — generate one (minisign -G) or pass --allow-unsigned"
fi
[ -f "$SYNC_SH" ] || die "$SYNC_SH not found"
[ -n "$VERSION" ] || die "$CHANGELOG has no '## [x.y.z]' entry — bump first"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1 \
    && die "Tag $TAG already exists — bump the version or remove the tag"
ok "git repo on $BRANCH, clean, gh authenticated, version $VERSION"

# ─── 1. Audit ───────────────────────────────────────────────────────────────
log "1. Audit (strict)"
if [ -n "$AUDIT_PROFILE" ]; then
    bash scripts/dev/audit/run_all.sh --profile "$AUDIT_PROFILE" --strict \
        || die "Audit failed (profile $AUDIT_PROFILE --strict) — fix before releasing"
    ok "Audit clean"
else
    warn "No audit profile under scripts/dev/audit/profiles/ — skipped"
fi

# ─── 2. Version sync ────────────────────────────────────────────────────────
log "2. Version sync"
if [ -n "$BUMP" ]; then
    bash "$SYNC_SH" --bump "$BUMP"
    VERSION=$(canon_version || true)
    TAG="v${VERSION:-?}"
else
    bash "$SYNC_SH" --check \
        || die "Version drift — run 'bash $SYNC_SH' or release with '--bump X.Y.Z'"
fi
ok "Version $VERSION (tag $TAG)"

# ─── 3. Feed ────────────────────────────────────────────────────────────────
log "3. Signed update feed"
bash "$SYNC_SH" --release-feed

# ─── 4. Optional build hook ─────────────────────────────────────────────────
if [ -n "${BUILD_CMD:-}" ]; then
    log "4. Build (BUILD_CMD)"
    bash -c "$BUILD_CMD" || die "BUILD_CMD failed: $BUILD_CMD"
    ok "Build done"
fi

# ─── 5. Commit + tag ────────────────────────────────────────────────────────
log "5. Commit and tag $TAG"
git add -u
[ -d feed ] && git add feed/ 2>/dev/null || true
if git diff --cached --quiet; then
    ok "Nothing to commit (already synced)"
else
    if git commit -S -m "chore(release): $TAG" 2>/dev/null; then
        ok "Signed commit (PGP)"
    else
        warn "PGP signing unavailable — committing unsigned"
        git commit -m "chore(release): $TAG"
    fi
fi
if git tag -s "$TAG" -m "Release $TAG" 2>/dev/null; then
    ok "Signed tag $TAG"
else
    warn "PGP signing unavailable — creating annotated (unsigned) tag"
    git tag -a "$TAG" -m "Release $TAG"
fi

# ─── 6. Package ─────────────────────────────────────────────────────────────
log "6. Package artifacts"
mkdir -p dist
PKG="$REPO_NAME-$TAG.tar.gz"
git archive --format=tar.gz --prefix="$REPO_NAME-$TAG/" -o "dist/$PKG" HEAD
ok "dist/$PKG"
( cd dist && sha256sum "$PKG" > "$PKG.sha256" )
ok "dist/$PKG.sha256"
ASSETS=("dist/$PKG" "dist/$PKG.sha256")
if [ -n "$MINISIGN_KEY" ] && command -v minisign >/dev/null 2>&1; then
    minisign -S -s "$MINISIGN_KEY" -m "dist/$PKG" \
        -t "$PRODUCT_NAME $TAG"
    ASSETS+=("dist/$PKG.minisig")
    ok "dist/$PKG.minisig (minisign)"
else
    warn "No minisign key (env RELEASE_MINISIGN_KEY, feed/minisign.key or minisign.key) — artifact unsigned"
fi

# ─── 7. Publish ─────────────────────────────────────────────────────────────
log "7. Publish $TAG"
if [ "$YES" != "1" ]; then
    printf '  Publish release %s (push + GitHub release)? [y/N]: ' "$TAG"
    read -r CONFIRM || CONFIRM="n"
    case "$CONFIRM" in y|Y) : ;; *) die "Publish cancelled by user" ;; esac
fi

NOTES_FILE=$(mktemp -t release-notes.XXXXXX)
trap 'rm -f "$NOTES_FILE"' EXIT
awk -v v="$VERSION" '
    /^## \[/ { if (f) exit; if (index($0, "[" v "]")) f = 1; next }
    f' "$CHANGELOG" > "$NOTES_FILE"
[ -s "$NOTES_FILE" ] || die "No release notes: $CHANGELOG lacks a '## [$VERSION]' section body"

git push origin "$BRANCH"
git push origin "$TAG"
ok "Pushed $BRANCH + $TAG"

gh_args=(--title "$PRODUCT_NAME $TAG" --notes-file "$NOTES_FILE")
[ -n "$GH_REPO" ] && gh_args+=(--repo "$GH_REPO")
gh release create "$TAG" "${gh_args[@]}" "${ASSETS[@]}"

# ─── 8. Summary ─────────────────────────────────────────────────────────────
log "8. Done"
echo "  Release : $TAG"
echo "  Assets  : ${ASSETS[*]}"
if [ -n "$GH_REPO" ]; then
    echo "  URL     : https://github.com/$GH_REPO/releases/tag/$TAG"
else
    gh release view "$TAG" --json url --jq .url 2>/dev/null || true
fi
