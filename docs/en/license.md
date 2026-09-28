---
layout: default
title: Licensing
lang: en
---
> **User document:** `docs/en/license.md`
> **Version:** 1.1 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** LICENSE · THIRD_PARTY_LICENSES.md

# Licensing

The license your project ships is **source-visible proprietary**: your code
stays visible in the repository, but private and non-redistributable.

---

## The license

The `LICENSE` file is a **template** (English + Spanish) that uses the same
double-brace placeholders as the rest of the kit:

| Placeholder | Value |
|-------------|-------|
| `{{ product_name }}` | Software name |
| `{{ owner }}` | Copyright holder (person or company) |
| `{{ email }}` | Contact for security reports and license matters |
| `{{ year }}` | Year(s) of publication |

When the project is generated, the generator substitutes all four
automatically from `config.json` — no manual step is needed. (They are written here as `{{ key }}` — with a space — so that this
document itself is not rewritten during generation; the real placeholders have
no spaces.)

If you instead copy `templates/LICENSE` by hand, run:

```bash
# The real tokens have no inner spaces; they are built here so this document
# stays renderable (a literal token would be substituted by the generator).
O='{{'; C='}}'
sed -i "s/${O}product_name${C}/Acme Widget/g; s/${O}owner${C}/Acme Corp/g; s/${O}email${C}/legal@example.com/g; s/${O}year${C}/2025/g" LICENSE
```

Do **not** remove the coordinated-disclosure clause (§5) or the integrity
notices.

## What the license grants and restricts

- **Granted** — view, read and compile the source for personal, non-commercial
  use; backup copies.
- **Restricted** — no commercial use, no redistribution, no derivative works,
  no competing products, no removal of notices.
- **Mandatory** — vulnerabilities must be reported privately within 72 hours
  (coordinated disclosure).

## Third-party licenses

Dependencies keep their own licenses and must be listed. Generate the notice
from the lockfile with the ecosystem tool:

| Ecosystem | Tool |
|-----------|------|
| Rust / Cargo | `cargo-about`, `cargo-deny` |
| Node / npm | `license-checker`, `npm-license-crawler` |
| Python | `pip-licenses` |
| Java / Maven | `license-maven-plugin` |
| Go | `go-licenses` |

Keep the notice in `THIRD_PARTY_LICENSES.md` (guide) → generated
`THIRD_PARTY_LICENSES.txt`. Audit for copyleft (GPL/AGPL) incompatibilities with
a proprietary project.

---

See also: [Preparing for distribution](distribution.md) · [Release signing](signing.md).
