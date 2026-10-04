---
layout: default
title: Release signing
lang: en
---
> **User document:** `docs/en/signing.md`
> **Version:** 1.5 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** license.md · distribution.md

# Release signing

Every release you publish gets **two signatures** — one classic, one
post-quantum — so anyone can verify your downloads **offline**, even years
later:

| Layer | Algorithm | Public key | Signature file |
|-------|-----------|------------|----------------|
| Classic | Ed25519 (minisign) | `minisign.pub` (repo root) | `<artifact>.tar.gz.minisig` |
| Post-quantum | ML-DSA-65 (FIPS 204) | `pqc_sign.pub` (repo root) | `<artifact>.tar.gz.pqsig` |

## How your users verify a download (offline)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# ML-DSA-65: verify <artifact>.tar.gz.pqsig against pqc_sign.pub
#   with any ML-DSA-65 verifier
```

If your project ships a CLI, you can also embed the public key in the binary
and offer a verify subcommand (`<product> verify <artifact>.tar.gz`) — an
optional convenience; the generic `.pqsig` + `pqc_sign.pub` check always works.

---

See also: [Licensing](license.md) · [Preparing for distribution](distribution.md).
