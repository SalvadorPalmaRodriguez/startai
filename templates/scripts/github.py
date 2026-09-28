#!/usr/bin/env python3
"""Publish the project to GitHub and enable GitHub Pages — from the console.

Subcommands:
    create   create the repo (if missing), configure About (homepage/topics),
             and add the `origin` remote.
    pages    enable GitHub Pages served from /docs on the given branch and
             trigger a build.
    status   show the Pages build status and the site URL.

Requires the GitHub CLI authenticated: https://cli.github.com/

Example:
    python3 scripts/github.py create --owner me --repo my-repo --description "My tool" --topic cli
    git add -A && git commit -m "Initial commit" && git push -u origin main
    python3 scripts/github.py pages --owner me --repo my-repo
    python3 scripts/github.py status --owner me --repo my-repo
"""

import argparse
import shutil
import subprocess
import sys


def run(cmd, check=True):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def gh(args, check=True):
    return run(["gh", *args], check=check)


def git(args, check=True):
    return run(["git", *args], check=check)


def check_environment():
    """Probe required tools before doing anything; exit 2 if not usable."""
    if shutil.which("gh") is None:
        print("ERROR: gh CLI not found — install it and run 'gh auth login'",
              file=sys.stderr)
        sys.exit(2)
    if shutil.which("git") is None:
        print("ERROR: git not found — install it and retry", file=sys.stderr)
        sys.exit(2)
    r = gh(["auth", "status"], check=False)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        print("ERROR: gh is not authenticated — run 'gh auth login' first"
              + (f"\n{detail}" if detail else ""), file=sys.stderr)
        sys.exit(2)


def warn_step(result, what):
    """Report a failed check=False call on stderr; return True if it failed."""
    if result.returncode == 0:
        return False
    detail = (result.stderr or result.stdout or "").strip()
    print(f"WARNING: {what} failed" + (f": {detail}" if detail else ""),
          file=sys.stderr)
    return True


def pages_url(owner, repo):
    # User/organization site repo: "owner.github.io" is served at the root,
    # not under a /{repo}/ path prefix.
    if repo.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner}.github.io/"
    return f"https://{owner}.github.io/{repo}/"


def repo_exists(owner, repo):
    return gh(["repo", "view", f"{owner}/{repo}"], check=False).returncode == 0


def create_repo_cmd(owner, repo, description, public):
    cmd = ["repo", "create", f"{owner}/{repo}", "--public" if public else "--private"]
    if description:
        cmd += ["--description", description]
    cmd += ["--homepage", pages_url(owner, repo)]
    return cmd


def set_topic_cmd(owner, repo, topic):
    return ["repo", "edit", f"{owner}/{repo}", "--add-topic", topic]


def enable_pages_cmd(owner, repo, branch, path):
    return ["api", f"repos/{owner}/{repo}/pages", "-X", "POST",
            "-f", f"source[branch]={branch}", "-f", f"source[path]={path}"]


def trigger_build_cmd(owner, repo):
    return ["api", f"repos/{owner}/{repo}/pages/builds", "-X", "POST"]


def build_status_cmd(owner, repo):
    return ["api", f"repos/{owner}/{repo}/pages/builds", "--jq", ".[0].status"]


def cmd_create(args):
    if repo_exists(args.owner, args.repo):
        print(f"Repo already exists: {args.owner}/{args.repo}")
        r = gh(["repo", "edit", f"{args.owner}/{args.repo}",
                "--homepage", pages_url(args.owner, args.repo)], check=False)
        warn_step(r, "updating homepage/description of the existing repo")
    else:
        gh(create_repo_cmd(args.owner, args.repo, args.description, not args.private))
        print(f"Repo created: {args.owner}/{args.repo}")
    topics_ok = True
    for topic in args.topic or []:
        r = gh(set_topic_cmd(args.owner, args.repo, topic), check=False)
        topics_ok = not warn_step(r, f"adding topic '{topic}'") and topics_ok
    if args.topic and topics_ok:
        print("Topics set.")
    if git(["remote", "get-url", "origin"], check=False).returncode != 0:
        git(["remote", "add", "origin", f"https://github.com/{args.owner}/{args.repo}.git"])
        print("Remote 'origin' added.")
    print("Next: git add -A && git commit -m 'Initial commit' && git push -u origin main")


def cmd_pages(args):
    failed = warn_step(
        gh(enable_pages_cmd(args.owner, args.repo, args.branch, "/docs"),
           check=False),
        "enabling GitHub Pages")
    failed = warn_step(
        gh(trigger_build_cmd(args.owner, args.repo), check=False),
        "triggering the first Pages build") or failed
    if failed:
        print("ERROR: Pages could not be fully enabled — see warnings above.",
              file=sys.stderr)
        sys.exit(1)
    print(f"Pages enabled: {pages_url(args.owner, args.repo)}")


def cmd_status(args):
    r = gh(build_status_cmd(args.owner, args.repo), check=False)
    if r.returncode != 0:
        warn_step(r, "querying the Pages build status")
        sys.exit(1)
    status = r.stdout.strip() or "(unknown — no builds yet)"
    print(f"Build status: {status}")
    print(f"Site: {pages_url(args.owner, args.repo)}")


def main():
    parser = argparse.ArgumentParser(
        description="Publish to GitHub and enable GitHub Pages from the console.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="create the repo (if missing), configure About, add origin remote")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--private", action="store_true", help="create a private repo (default: public)")
    p.add_argument("--topic", action="append", help="add a repo topic (repeatable)")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("pages", help="enable GitHub Pages from /docs and trigger a build")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", default="main")
    p.set_defaults(func=cmd_pages)

    p = sub.add_parser("status", help="show Pages build status and site URL")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.set_defaults(func=cmd_status)

    args = parser.parse_args()
    check_environment()
    args.func(args)


if __name__ == "__main__":
    main()
