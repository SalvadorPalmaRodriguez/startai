---
layout: default
title: Release signing
lang: en
---
> **User document:** `docs/en/signing.md`
> **Version:** 1.3 | **Updated:** 2026-09-28
> **Status:** ✅ **CURRENT**
> **References:** `signing` skill

# Release signing

The kit sets up a dual-signature model for releases — one classic layer and
one post-quantum layer — so users can verify a download **offline**:

| Layer | Algorithm | Private key | Public key |
|-------|-----------|-------------|------------|
| Classic | Ed25519 (minisign) | outside the repo, `0600` + passphrase | `minisign.pub` (repo root) |
| Post-quantum | ML-DSA-65 (FIPS 204) | outside the repo, `0600` + passphrase | `pqc_sign.pub` (repo root) |

Private keys are **never committed**; they live outside the repository with
`0600` permissions and a passphrase.

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

The signing ceremony and key rotation are owner-side processes; they live in
the `signing` skill, not in this public guide.

---

See also: [Licensing](license.md) · [Preparing for distribution](distribution.md).
