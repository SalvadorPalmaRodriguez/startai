# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `startai.py adopt`: layered adoption of the kit into existing projects —
  preflight doctor with BLOCKER/WARN findings (colliding template tokens,
  tracked private paths, pre-existing git hooks, conflicting docs
  generators, bilingual parity, audit prerequisites), `.startai-new`
  conflict diversion, managed idempotent `.gitignore` block on every apply
  (`.devinignore` with the `agents` layer), `.startai-adopt.json` manifest
  for idempotent re-runs, opt-in enforcement (hooks never auto-installed),
  `--emit-dir` staging renders that never touch the target, and a two-phase
  `--manual` checklist mode (render first, then copy).
- GitHub issue forms (bug report, feature request, contact links) in
  `.github/ISSUE_TEMPLATE/` and in the scaffold via
  `templates/.github/ISSUE_TEMPLATE/`.
- Optional agent-orchestrator contract in the scaffold:
  `templates/.agents/orchestrator/` (config, generic roles, declarative
  workflows, memory/state directories).
- `scripts/github.py`: preflight probe for `gh`/`git` and `gh auth status`,
  readable errors, uniform `returncode` handling for `check=False` calls,
  correct Pages URL for user/organization site repos (`owner.github.io`).
- Wizard: real multiline input for keys with multiline defaults
  (`command_tree`, `dir_structure`), ended by an empty line.
- `THIRD_PARTY_LICENSES.md` now states that startai has no third-party
  runtime dependencies (Python standard library only).

### Fixed
- Audit check 17 (`docs_sync_markers`): false positives on self-referential
  mentions of the `[PENDIENTE]` convention (backticked tokens, skill
  `description:` frontmatter). New optional profile variable
  `MARKER_IGNORE_RE` filters matching hit lines before counting; empty =
  previous behaviour.

## [0.1.0] - 2026-09-27

### Added
- First (alpha) release of the `startai` documentation kit.
- Guide: turning a normal project into an AI-native project (`AGENTS.md`,
  `.agents/` with `agents/` and `skills/`, `llms.txt` / `llms-full.txt`,
  public/private split via `.gitignore` + `.devinignore`).
- Guide: preparing a project for distribution (bilingual README, demo GIF,
  GitHub Pages static site, GitHub "About" section, visibility/promotion).
- Source-visible proprietary `LICENSE` template (English + Spanish, placeholder
  name) and third-party licenses guide.
- Release signing documentation: minisign (Ed25519) + post-quantum ML-DSA-65.
- Bilingual GitHub Pages skeleton (Jekyll, `theme: null`, custom layout with
  EN/ES language switcher, social preview).
