# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-10-04

### Added
- Initial release of `startai`: an agnostic documentation-and-templates kit to
  make a project AI-native and distribution-ready.
- AI-native conversion: `AGENTS.md` + `.agents/` (skills and agent roles),
  `llms.txt` / `llms-full.txt`, public/private split, and the
  `ai_files_visibility` flag (`private` default / `public`) via sentinel blocks.
- Layered adoption (`startai.py adopt`) with a preflight doctor, idempotent
  `.gitignore` management, `.startai-adopt.json` manifest and `.startai-new`
  conflict diversion.
- Distribution prep: bilingual EN/ES README and GitHub Pages static site
  (Jekyll, language switcher, social preview), demo GIF, About section,
  source-visible proprietary `LICENSE` and `THIRD_PARTY_LICENSES.md`.
- Signed release pipeline: strict audit gate, semver sync from `CHANGELOG.md`,
  signed tag, tarball with sha256 + minisign (Ed25519) + ML-DSA-65, and a
  signed update feed (`feed/advisories.json` + `.minisig`).
- Anti-leak guards: git hooks (`pre-commit`, `commit-msg`, `pre-push`) and
  audit checks for secrets, private paths, and owner-private terms loaded at
  runtime from a gitignored conf.
- `scripts/github.py` (repo creation, GitHub Pages enable) and a project
  wizard; optional agent-orchestrator contract in
  `templates/.agents/orchestrator/`.

### Fixed
- Owner-private terms are no longer hardcoded in public hook sources; they load
  at runtime from a gitignored conf.
- Adopt preflight no longer false-positives on the generated `scripts/check.py`.
