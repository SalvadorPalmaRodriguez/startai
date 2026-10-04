# scripts/dev/audit/ — Unified audit framework

Audit and coherence-verification scripts for the repository. Private tooling:
this whole directory is gitignored (`/scripts/dev/`).

## Usage

```bash
bash scripts/dev/audit/run_all.sh --profile project            # normal audit
bash scripts/dev/audit/run_all.sh --profile project --strict   # warnings block (exit 2)
bash scripts/dev/audit/run_all.sh --profile project --output /tmp/audit.log
bash scripts/dev/audit/run_all.sh --profile project --json /tmp/audit.json
bash scripts/dev/audit/run_all.sh --profile project --project-root /other/repo
```

| Option | Description | Default |
|--------|-------------|---------|
| `--profile <name>` | Check profile (`profiles/<name>.conf`) | required |
| `--project-root <path>` | Project root to audit | repo root |
| `--strict` | Exit 2 on warnings | false |
| `--output <path>` | Full transcript without ANSI | — |
| `--json <path>` | JSON report per check + totals | — |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Clean (or warnings without --strict) |
| 1 | Blocking errors (includes check infrastructure failures) |
| 2 | Warnings only, with --strict |

## AUDIT_RESULT contract

Every check ends with `audit_exit` (`lib/common.sh`), which prints a sentinel
line `AUDIT_RESULT check=<n> errors=<N> warnings=<N> infos=<N>` before
exiting. `run_all.sh` uses it as the source of truth for counters, contrasts
the real exit code with the expected one, and cross-checks the declared
counters against the actually printed `❌ ERROR:`/`⚠️  WARN:` lines (catches
`log_*` lost in pipe subshells). A check that aborts without a sentinel counts
as an infrastructure error.

## Layout

| Path | Role |
|------|------|
| `run_all.sh` | Orchestrator: profiles, flags, sentinel parsing, summary, JSON |
| `lib/common.sh` | `log_*`, `audit_exit`, `audit_is_git_repo`, `audit_source_profile` |
| `checks/NN_*.sh` | Individual checks — **generic**, policy-free |
| `profiles/*.conf` | Per-repo policy: check list + all paths/lists as variables |

All repo-specific policy (scan dirs, private-path lists, version targets)
lives in the profile `.conf` — the checks only read those variables. This is
what lets `templates/scripts/dev/audit/` be an identical copy except for
`profiles/project.conf`.

Escape hatch: `MARKER_IGNORE_RE` (check 17) filters self-referential marker
mentions — see its header comment for the accepted trade-off.

Check 24 (`public_doc_refs`) flags private-path references in public docs:
R1 errors on any private path in a `References`/`Referencias` header line;
R2 errors on private paths elsewhere unless the file is listed in the
profile's `PUBLIC_DOC_PRIVATE_REF_ALLOW`. Needles are derived from
`PRIVATE_GLOBS` and `templates/` is out of scope.
