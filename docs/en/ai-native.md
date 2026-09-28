---
layout: default
title: Making a project AI-native
lang: en
---
> **User document:** `docs/en/ai-native.md`
> **Version:** 1.3 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** distribution.md

# Making a project AI-native

This guide turns your project into one where an AI agent can work natively
and consistently. The key idea: **your rules live in one place, and agents
discover them through standard files.**

---

## 1. `AGENTS.md` at the root

This is the **canonical entry point** for any AI agent (Copilot, Cursor, Claude
Code, Codex, Cline, Devin, Windsurf, Aider…). It contains:

- **Identity** — what the project is, its language and architecture.
- **Invariants** — the minimal rules every agent must respect.
- **Rules → skill table** — maps each topic to the skill that holds the details.
- **Skills index** — the list of `.agents/skills/*`.

```markdown
# AGENTS.md — universal rules for AI agents

> Read first, edit later. Canonical entry point for ANY AI agent.

## Rules
| Topic | Minimal rule | Skill |
|-------|--------------|-------|
| Commits | Sign with `git commit -S` | security |
```

## 2. Nested `AGENTS.md` (only where needed)

Add `**/AGENTS.md` **only** in directories with specific rules. Never duplicate
the root index; the nested file references the root and adds only what is local.

## 3. `.agents/skills/<name>/SKILL.md`

Self-contained domain skills (standard `agentskills.io`). Each one starts with
frontmatter so tools can discover it by `description`:

```markdown
---
name: security
description: PGP commits, secrets, audit, coordinated disclosure
---

# Security
## When to use this skill
...
```

**Golden rule:** `AGENTS.md` + `SKILL.md` are the only home for rules and
lessons. Everything else references them — never copies.

## 4. `.agents/agents/<name>.md`

Agent roles — "who does what" (developer, reviewer, security…). Separate the
*role* (persona) from the *skill* (domain capability).

## 5. `.agents/README.md`

The "Project Brain": explains the structure, the golden rule, and what is
public vs private.

## 6. `llms.txt` and `llms-full.txt`

Public, versioned AI context:

- `llms.txt` — short index for AI crawlers: what the project is, legal notes,
  links to documentation.
- `llms-full.txt` — expanded single-file context.

Always include: *"AI readability does NOT constitute a license grant."*

## 7. Public / private split

- **`.gitignore`** — ignore `**/AGENTS.md`, `.agents/`, `CLAUDE.md`, `.claude/`,
  personal notes/plans, dev tooling, and secrets.
- **`.devinignore`** — a gitignored file with `!` negations that un-ignore
  private paths **only for agent tools** (read/edit/grep). Git never reads it,
  so nothing private can be staged. **Never** negate secrets or build artifacts.

## 8. Optional: bridge and orchestrator

- `CLAUDE.md` with `@AGENTS.md` for Claude Code.
- A custom orchestrator (`roles/`, `workflows/`, `memory/`, `state/`) if the
  team uses an orchestrating dev-agent.

## 9. Adopting in an existing project

When the project already exists, the kit is applied **in layers** instead of
scaffolding from scratch. The adoption flow:

1. **Preflight first**: inspect the repo for things that would break later —
   template tokens (`{{ x }}`/`{ALL-CAPS}`) that the coherence check would
   reject on every commit, private paths already tracked by git, pre-existing
   git hooks, conflicting docs generators, missing bilingual parity.
2. **Apply by layers**: `agents` (AI context) → `hooks` → `audit` → `docs` →
   `distribution` → `release`. Conflicting files are never overwritten; they
   are diverted to `<path>.startai-new` for manual merging.
3. **Enforcement stays opt-in**: git hooks are shipped but never installed
   automatically; audit profile entries for files that don't exist yet are
   commented out, not deleted.
4. **Additive private split**: `.gitignore` always gets a marked,
   idempotent managed block (the adoption manifest must stay ignored);
   `.devinignore` gets one only with the `agents` layer — user lines are
   never touched.
5. **Manifest**: a `.startai-adopt.json` records adopted layers and file
   hashes, so re-running adoption is idempotent and can upgrade kit-owned
   files while leaving user-edited ones alone.

A manual checklist is an equally supported path when you prefer full
control — but it is two-phase: kit files are rendered into a staging
directory first (never copied straight from `templates/`, which carries
unresolved placeholders), then copied into place, and the marked
`.gitignore` block is appended so the adoption manifest stays private.
Appending by hand is not idempotent: on a repeat manual adoption, remove
the previous marked block first so you do not end up with two.

---

See also: [Preparing for distribution](distribution.md) · [Licensing](license.md).
