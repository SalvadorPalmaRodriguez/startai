---
layout: default
title: Preparing a project for distribution
lang: en
---
> **User document:** `docs/en/distribution.md`
> **Version:** 1.4 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** README.md · ai-native.md

# Preparing a project for distribution

The distribution artifacts this kit ships as templates, and how to fill them
in for your project.

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

## 2. What the kit ships

- **Bilingual static site skeleton** — a `docs/` site (config, custom layout
  with the EN/ES language switcher, styles) ready for GitHub Pages.
- **`docs/assets/social-preview.svg`** — a 1280×640 template for the
  link-preview card; edit the texts and export it to PNG.
- **Community and legal templates** — `SECURITY.md`, `CONTRIBUTING.md`,
  `CHANGELOG.md` (Keep a Changelog), `LICENSE` and `THIRD_PARTY_LICENSES.md`.
- **`llms.txt` / `llms-full.txt`** — context files for AI indexers, with the
  legal note already included.
- The repo is meant to be public (source-visible), and releases go out with
  dual signatures (see [Release signing](signing.md)).

---

See also: [Making a project AI-native](ai-native.md) · [Licensing](license.md).
