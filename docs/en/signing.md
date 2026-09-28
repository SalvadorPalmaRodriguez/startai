---
layout: default
title: Release signing
lang: en
---
> **User document:** `docs/en/signing.md`
> **Version:** 1.4 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** license.md · distribution.md

# Release signing

The kit sets up a dual-signature model for releases — one classic layer and
one post-quantum layer — so users can verify a download **offline**:

| Layer | Algorithm | Public key | Signature file |
|-------|-----------|------------|----------------|
| Classic | Ed25519 (minisign) | `minisign.pub` (repo root) | `<artifact>.tar.gz.minisig` |
| Post-quantum | ML-DSA-65 (FIPS 204) | `pqc_sign.pub` (repo root) | `<artifact>.tar.gz.pqsig` |

## Verifying a download (offline)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# ML-DSA-65: verify <artifact>.tar.gz.pqsig against pqc_sign.pub
#   with any ML-DSA-65 verifier
```

For projects that ship a CLI, embedding the public key in the binary and
exposing a verify subcommand (`<product> verify <artifact>.tar.gz`) is an
optional convenience — the generic `.pqsig` + `pqc_sign.pub` check always works.

---

See also: [Licensing](license.md) · [Preparing for distribution](distribution.md).
