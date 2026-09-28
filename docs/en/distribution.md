---
layout: default
title: Preparing a project for distribution
lang: en
---
> **User document:** `docs/en/distribution.md`
> **Version:** 1.1 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** README.md · `distribution` skill

# Preparing a project for distribution

How to leave a project ready for distribution in a repository, with the same
visibility and promotion sections as a polished public repo.

---

## 1. Bilingual README (EN/ES)

`README.md` (EN) and `README.es.md` (ES), linked to each other in the header.

Standard structure:

```
# {{ product_name }} — {{ tagline }}
**English** · **[Español](README.es.md)**

[badges: version, license, platform, language]
![demo GIF](docs/demo.gif)

> one-line pitch + 3 key points + docs link + llms.txt note

## Features
## Architecture
## Table of Contents
## Installation
## Usage
## License
```

## 2. Demo GIF

Record a terminal session and render it to a GIF:

```bash
asciinema rec docs/demo.cast      # record
agg docs/demo.cast docs/demo.gif  # render to GIF
```

Commit the `.gif` (plus the `.cast` and the script that produces it) under
`docs/`. Reference it from the README and the static site home.

## 3. GitHub "About" section

In the repository settings (About), set:

- **Description** — one sentence with keywords.
- **Website** — the GitHub Pages URL: `https://<owner>.github.io/<repo>/`.
- **Topics** — discovery tags (language, domain, `cli`, `docs`, …).

## 4. Static site (GitHub Pages)

Publish from `docs/` with Jekyll (see the `github-pages` skill).
Set: Settings → Pages → Source → Deploy from branch → `/docs`.

## 5. Social preview / Open Graph

Create a 1280×640 image (`docs/assets/social-preview.svg`) and upload it as PNG
in Settings → Social preview, so links render a nice card.

## 6. Visibility and promotion

- Repository public (source-visible).
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.
- Signed releases (see [Release signing](signing.md)) and `llms.txt` for AI.

---

See also: [Making a project AI-native](ai-native.md) · [Licensing](license.md).
