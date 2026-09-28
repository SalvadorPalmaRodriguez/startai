---
layout: default
title: Release signing
lang: en
---
> **User document:** `docs/en/signing.md`
> **Version:** 1.0 | **Updated:** 2026-09-27
> **Status:** ✅ **CURRENT**
> **References:** .agents/skills/signing/SKILL.md

# Release signing

Every release is signed twice to verify authenticity — including offline:

| Layer | Algorithm | Private key | Public key |
|-------|-----------|-------------|------------|
| Classic | Ed25519 (minisign) | `~/.minisign/<product>.key` | `minisign.pub` (repo root) |
| Post-quantum | ML-DSA-65 (FIPS 204) | `~/.<product>/pqc_signing.key` | `pqc_sign.pub` (repo root) |

Private keys are **never committed**; they live outside the repo with `0600`
permissions and a passphrase.

---

## Signing ceremony

1. **Reproducible build** — compile with neutral paths (no `/home/<user>`).
2. **Package** — tarball the artifact.
3. **SHA256** — `sha256sum <artifact>.tar.gz`.
4. **minisign** — `minisign -S -m <artifact>.tar.gz -s ~/.minisign/<product>.key`.
5. **PQC** — sign with ML-DSA-65 → `<artifact>.tar.gz.pqsig`.
6. **Local verification** — verify minisign, PQC and SHA256 before publishing.
7. **SBOM** — generate the Software Bill of Materials (SPDX).
8. **Publish** — upload artifact + signatures + SBOM to GitHub Releases.
9. **Re-sign the update feed** (if any) with minisign.
10. **Tag** — `git tag -s` (PGP) and push.
11. **Cleanup** — remove temporary files.

## Verification by the user (offline)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# post-quantum (ML-DSA-65), key embedded in the binary
<product> verify <artifact>.tar.gz
```

## Key rotation

1. Generate a new key (`minisign -G`).
2. Sign the new public key with the current key.
3. Announce it in the feed (`next_pubkey`) if one exists.
4. Wait one update cycle for clients to persist the new key.
5. Rotate the signing key on the next release and update `minisign.pub` + the
   embedded key.

---

See also: [Licensing](license.md) · [Preparing for distribution](distribution.md).
