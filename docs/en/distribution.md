---
layout: default
title: Preparing your project for distribution
lang: en
---
> **User document:** `docs/en/distribution.md`
> **Version:** 1.7 | **Updated:** 2026-10-04
> **Status:** ✅ **CURRENT**
> **References:** README.md · ai-native.md

# Preparing your project for distribution

What your new project ships out of the box — and how to fill in each template
with your own values.

---

## Bilingual README (EN/ES)

`README.md` (EN) and `README.es.md` (ES), linked to each other in the header.

Standard structure (the placeholders are written spaced — `{{ name }}` — so
this page renders; the real tokens have no inner spaces):

```
# {{ product_name }} — {{ tagline }}
**English** · **[Español](README.es.md)**

[badges: version, license, platform, language]
<!-- record with `asciinema rec docs/demo.cast` + `agg docs/demo.cast docs/demo.gif`, then uncomment:
![demo GIF](docs/demo.gif)
-->

> one-line pitch + 3 key points + docs link + llms.txt note

## Features
## Architecture
## Table of Contents
## Installation
## Usage
## License
```

The demo GIF ships commented out on purpose: record a terminal session with
`asciinema`, render it with `agg`, commit `docs/demo.gif`, then uncomment the
line. Set the repo's About section (description + homepage + topics) while
you are at it — `python3 scripts/github.py create` does it from the console.

## What your project ships

- **Bilingual static site skeleton** — a `docs/` site (config, custom layout
  with the EN/ES language switcher, styles) ready for GitHub Pages. Enable it
  with `python3 scripts/github.py pages --owner <user> --repo <repo>`;
  preview locally with `bundle exec jekyll serve` inside `docs/`.
- **Language switcher** — page pairs are hardcoded in the `{% raw %}{% case %}{% endraw %}` map of
  `docs/_layouts/default.html`; when you add a page, add its EN/ES pair there
  or the switcher falls back to the language index.
- **`docs/assets/social-preview.svg`** — a 1280×640 template for the
  link-preview card; edit the texts and export it to PNG.
- **Community and legal templates** — `SECURITY.md`, `CONTRIBUTING.md`,
  `CHANGELOG.md` (Keep a Changelog), `LICENSE` and `THIRD_PARTY_LICENSES.md`.
- **`.github/`** — public issue templates (bug, feature, contact links).
- **Signed update feed** — `feed/` (`advisories.json` + README): the
  minisign-signed index your users check for new versions; `feed/minisign.key`
  stays private.
- **Project tooling** — `scripts/check.py`, `scripts/github.py`,
  `scripts/git/` hooks (opt-in), plus a private audit and release toolkit
  (kept out of git by the generated `.gitignore`).
- **`llms.txt` / `llms-full.txt`** — context files for AI indexers, with the
  legal note already included.
- Your repo is meant to be public (source-visible), and your releases go out
  with dual signatures (see [Release signing](signing.md)).

---

See also: [Making a project AI-native](ai-native.md) · [Licensing](license.md).
