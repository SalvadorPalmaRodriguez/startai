# Security Policy

## Reporting a Vulnerability

**Do NOT open a public issue for security problems.**

If you discover a security vulnerability, bug, misconfiguration or weakness
affecting the security, stability, integrity, confidentiality or availability
of this software, you must report it **privately and exclusively** to:

📧 **{{email}}**

- Report within **72 hours** of discovery.
- Public disclosure (issues, forums, social media, blogs, conferences) is
  **prohibited** until the issue has been remediated and written consent is
  given. This coordinated-disclosure embargo protects users from exploitation
  and is a binding condition of the [LICENSE](LICENSE) (§5).
- You will receive an acknowledgment and status updates by email.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | ✅ |
| Older builds | ❌ |

Only the latest published release receives security fixes. Check for updates
using the project's update mechanism.

## Verifying Downloads

Every release is signed twice:

- **minisign (Ed25519)** — classic signature, verified automatically by the installer.
- **ML-DSA-65 (FIPS 204)** — post-quantum signature, verified offline with the key embedded in the binary.

```bash
# Example: verify a downloaded release artifact
{{product_slug}} verify {{product_slug}}-vX.Y.Z-x86_64-linux.tar.gz
```

Full guide: [docs/en/signing.md](docs/en/signing.md) · [docs/es/signing.md](docs/es/signing.md)

## Security Model

- Source is **visible** (you can read and audit it) but **proprietary** — see [LICENSE](LICENSE).
- Releases are dual-signed and verifiable offline.
- Vulnerabilities are handled via **coordinated disclosure** only.

