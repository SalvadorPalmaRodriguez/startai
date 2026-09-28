# startai — AI-native & distribution-ready project kit

**English** · **[Español](README.es.md)**

> A documentation repository of **reusable, project-agnostic** processes and templates that answer two questions:
>
> 1. **How do I turn a normal project into an AI-native project?** — `AGENTS.md`, `.agents/` (agents + skills), `llms.txt` / `llms-full.txt`, and the public/private split so AI agents can work without leaking secrets.
> 2. **How do I leave a project ready for distribution in a repository?** — bilingual `README` + static-site templates, distribution artifacts, visibility/promotion, licensing and a dual release-signing model.

Everything here is **config-driven**: project-specific values live in a single config file (`config.example.json`), and the interactive scaffolder `scripts/startai.py` generates a new project from them — no manual placeholder hunting.

---

## What's inside

| Area | Where | Purpose |
|------|-------|---------|
| AI-native development | `templates/AGENTS.md`, `templates/.agents/`, `templates/llms.txt`, `templates/llms-full.txt` | Rules, skills and agent roles scaffolded into new projects (private there, via `templates/.gitignore`). |
| Distribution & promotion | `README.md`, `docs/`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | Bilingual README, bilingual static-site templates, community/legal files. |
| Licensing | `LICENSE`, `THIRD_PARTY_LICENSES.md` | Source-visible proprietary license (placeholder name) + third-party notices. |
| Release signing | `templates/.agents/skills/signing/`, `docs/*/signing.md` | dual signature model (minisign Ed25519 + post-quantum ML-DSA-65) and offline verification. |
| Config & scaffolding | `config.example.json`, `scripts/startai.py` | Single source of truth for variables + interactive generator. |
| Copy-paste templates | `templates/` | Project-identity templates rendered by the scaffolder. |

## The two core guides

- **[Making a project AI-native](docs/en/ai-native.md)** ([ES](docs/es/ai-native.md)) — the exact process, step by step.
- **[Preparing a project for distribution](docs/en/distribution.md)** ([ES](docs/es/distribution.md)) — README and site templates, distribution artifacts, visibility and promotion.

## Scaffolding a new project

```bash
python3 scripts/startai.py mi-proyecto                          # interactive
python3 scripts/startai.py mi-proyecto --config config.json     # non-interactive
python3 scripts/startai.py mi-proyecto --config config.json --dry-run                # preview
python3 scripts/startai.py mi-proyecto --config config.json --dry-run --dry-run-output preview.txt  # preview + save
python3 scripts/startai.py mi-proyecto --config config.json --strict                  # fail on empty values
python3 scripts/startai.py mi-proyecto --no-review              # skip the review
python3 scripts/startai.py --check                             # validate config + templates
```

`python3 scripts/startai.py --help` lists every option; `scripts/github.py --help`
lists the publishing subcommands.

The script (Python 3, no dependencies) asks for each variable, renders the
templates into a new directory, and walks every generated file. In the review,
each file can be `[k]` kept, `[e]` edited with your editor, `[r]` replaced with
an existing file (you give its path), or `[s]` skipped. With `--config` it reads
a JSON config and renders without asking anything.

The positional argument is the **target directory**: any relative or absolute
path, not just a name — `python3 scripts/startai.py ../mi-proyecto` creates the
project next to this kit instead of inside it (recommended). If omitted, it
defaults to `product_slug` from the config. The directory must be empty or not
exist; the script aborts otherwise. After rendering, the resolved config is
saved to `<target>/config.json` so the project can be regenerated later.

The configuration is always validated: empty or missing values print a
`WARNING` (with `--strict` they abort instead). `--dry-run` shows the resolved
configuration and the full rendered content of every file without writing
anything to disk; add `--dry-run-output FILE` to also save the preview.

Generated projects also ship the re-used tooling, all versioned/public:
`scripts/check.py` (coherence checks), `scripts/github.py` (publishing) and
`scripts/git/` (git hooks — install with `bash scripts/git/install-hooks.sh`).
They also ship `scripts/dev/` (audit framework, `session_start.sh`,
`context-gen.py`, `sync_version.sh`, `release.sh`), which the generated
`.gitignore` keeps private — dev tooling travels with the project but is not
published.

## Adopting the kit in an existing project

`startai.py adopt` brings selected layers of the kit into a project that
already exists (the `new` scaffold refuses non-empty directories). Two safety
rules are baked in: **adopt never writes without `--apply`**, and it **never
overwrites** a conflicting file — it writes `<path>.startai-new` instead — nor
does it install git hooks (enforcement is always opt-in).

```bash
python3 scripts/startai.py adopt /path/to/project --report                  # preflight only (default)
python3 scripts/startai.py adopt /path/to/project --apply --layers agents   # write one layer
python3 scripts/startai.py adopt --list-layers                              # layer table
python3 scripts/startai.py adopt /path/to/project --manual                  # manual checklist
python3 scripts/startai.py adopt /path/to/project --emit-dir /tmp/staging   # render into DIR, target untouched
python3 scripts/startai.py adopt /path/to/project --apply --force           # proceed past BLOCKERs
python3 scripts/startai.py adopt /path/to/project --apply --overwrite       # replace conflicts
python3 scripts/startai.py adopt /path/to/project --strict                  # warnings block too
```

### Layers

| Layer | Content | Risk |
|-------|---------|------|
| `agents` (default) | `AGENTS.md`, `.agents/` (skills, roles, orchestrator), `llms.txt`, `llms-full.txt`, `.devinignore` block | low — additive only |
| `hooks` | `scripts/git/` hooks + `scripts/check.py` | high — blocks commits if tokens or private paths collide (preflight detects it) |
| `audit` | `scripts/dev/` audit framework | medium — strict profile warns on missing CHANGELOG/README.es/llms-full |
| `docs` | bilingual EN/ES Jekyll site in `docs/` | high — collides with mkdocs/Docusaurus/Sphinx |
| `distribution` | `README*.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `THIRD_PARTY_LICENSES.md`, `.github/` | high — likely conflicts with existing files |
| `release` | `feed/`, `scripts/github.py` (requires `audit`) | medium |

Recommended flow: `--report` → fix/deselect around BLOCKERs →
`--apply --layers agents` → add layers incrementally. A `.startai-adopt.json`
manifest records hashes and adopted layers, so re-running adopt later is
idempotent and upgrades only files you haven't edited since.

The `.gitignore` managed block is applied on **every** `--apply` regardless
of the selected layers (the manifest itself must stay ignored), while
`.devinignore` is only touched by the `agents` layer.

`--emit-dir DIR` renders the selected layers into `DIR` **without touching
the target** — use it to diff the staged output against your repo with your
own tools, or as the first step of manual adoption. This does not violate
the "no writes without `--apply`" rule: it only writes to the directory you
explicitly name, never to the target.

Exit codes: `0` clean · `1` BLOCKERs present, or WARNINGs with `--strict`
(even when the write completed) · `2` usage error (unknown layer, missing
target).

### Preflight checks (why they exist)

- **Colliding `{{token}}`/`{ALLCAPS}` placeholders** (BLOCKER): `check.py`
  would fail every commit on Jekyll/Handlebars/Go-template syntax.
- **Private paths already tracked by git** (BLOCKER): pre-commit step 3 and
  audit check 23 would hard-fail (`AGENTS.md`, `.agents/`, `*.key`, …).
- **Existing `.git/hooks/` scripts or `core.hooksPath`** (BLOCKER/WARN):
  `install-hooks.sh` would overwrite them or be silently ignored.
- **Docs generator already present** (BLOCKER): mkdocs, Docusaurus,
  Sphinx/Jekyll config, or a docs framework in `package.json`.
- **Bilingual parity, audit prerequisites, dirty tree** (WARN): what the
  strict profile will complain about later.
- **Layer dependencies** (BLOCKER): e.g. `release` without `audit`.

### Manual adoption

`--manual` prints a copy/paste checklist derived from the same layer
manifest. It is a two-phase flow — never `cp` from `templates/` directly
(those files carry unresolved `{{tokens}}` that `check.py` would reject):
first render with `--emit-dir`, then copy the rendered files into place and
append the marked `.gitignore`/`.devinignore` blocks. It is a supported
path, but without the manifest re-runs cannot distinguish kit-owned files
from your edits — run `--report` first either way. One consequence: the
appending step is not idempotent the way `--apply` is, so on a repeat
manual adoption delete the existing `# >>> startai >>>` block before
appending the new one, or you will end up with two.

## Reference structure

```
project/
├── AGENTS.md              # canonical entry point for any AI agent (rules + skills index)
├── README.md / README.es.md
├── llms.txt / llms-full.txt        # AI-readable public context
├── LICENSE                # source-visible proprietary (bilingual, placeholder name)
├── THIRD_PARTY_LICENSES.md
├── SECURITY.md · CONTRIBUTING.md · CHANGELOG.md
├── .gitignore · .devinignore       # public/private split
├── .github/ISSUE_TEMPLATE/  # public issue forms (bug, feature, contact links)
├── .agents/
│   ├── agents/            # agent roles (who does what)
│   ├── skills/<name>/SKILL.md      # self-contained domain skills
│   └── orchestrator/      # optional agent-orchestrator contract (roles, workflows, memory)
└── docs/                  # GitHub Pages static site (Jekyll, bilingual EN/ES)
    ├── _config.yml
    ├── _layouts/default.html
    ├── assets/            # css, logo, social preview
    ├── en/                # English guides
    └── es/                # Spanish guides
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

A test suite in three layers — **unit** (token substitution, config loading,
validation, review actions, GitHub command construction), **integration**
(scaffolded tree, template/config coherence, no unresolved tokens, gitignore
split, script executability, `check.py`) and **end-to-end** (CLI modes:
`--help`, `--config`, `--dry-run`, `--dry-run-output`, `--strict`, `--check`,
wizard, empty-value warning, non-empty target guard).

## Publishing to GitHub

Everything from the console — no browser needed. Requires the GitHub CLI (`gh`):

1. Install the git hooks (validation + anti-secret + no AI-attribution commits):
   ```bash
   bash scripts/git/install-hooks.sh
   ```

2. Create the repo, configure About (homepage + topics) and the `origin` remote:
   ```bash
   python3 scripts/github.py create --owner <user> --repo <repo> --description "..." --topic cli
   ```

3. Commit and push:
   ```bash
   git add -A && git commit -m "Initial commit" && git push -u origin main
   ```

4. Enable GitHub Pages (served from `docs/`) and trigger a build:
   ```bash
   python3 scripts/github.py pages --owner <user> --repo <repo>
   python3 scripts/github.py status --owner <user> --repo <repo>
   ```

Your site is live at `https://<user>.github.io/<repo>/`.

## License

`startai` itself is licensed under a **source-visible proprietary** license:
private, code-visible, personal use only — see [LICENSE](LICENSE). The
scaffolder generates that same license for new projects from
`templates/LICENSE`, filling its `{{product_name}}`, `{{owner}}`, `{{email}}`
and `{{year}}` variables from `config.example.json`. See the [license guide](docs/en/license.md).

---

📄 **[llms.txt](llms.txt)** for AI indexers — AI readability does **not** constitute a license grant; see [LICENSE](LICENSE).
