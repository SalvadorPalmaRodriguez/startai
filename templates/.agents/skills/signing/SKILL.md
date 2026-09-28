---
name: signing
description: Release signing ceremony with minisign (Ed25519) and post-quantum ML-DSA-65 (FIPS 204), key management, offline verification, key rotation
---

# Signing

## Cuándo usar esta skill
- Firmar un release o artefacto distribuido.
- Gestionar las claves de firma (minisign + PQC) y su rotación.
- Documentar a los usuarios cómo verificar las descargas.

## Modelo de firma: doble capa

| Capa | Algoritmo | Clave privada | Clave pública | Herramienta |
|------|-----------|---------------|---------------|-------------|
| Clásica | Ed25519 | `~/.minisign/<product>.key` | `minisign.pub` (raíz repo) | `minisign` |
| Post-cuántica | ML-DSA-65 (FIPS 204) | `~/.<product>/pqc_signing.key` | `pqc_sign.pub` (raíz repo) | herramienta PQC propia |

- Las **claves privadas NUNCA se commitean**; viven fuera del repo con permisos
  `0600` y passphrase.
- Las claves públicas se publican en la raíz del repo (y/o se embeben en el
  binario como trust anchor).

## Ceremonia de firma (pasos)

1. **Build reproducible** — compilar con rutas neutras (sin `/home/<user>`).
2. **Empaquetar** — tarball del artefacto.
3. **SHA256** — `sha256sum` del artefacto.
4. **Firma minisign** — `minisign -S -m <file> -s ~/.minisign/<product>.key`.
5. **Firma PQC** — firmar con ML-DSA-65 → `.pqsig`.
6. **Verificación local** — verificar minisign (`-Vm -p minisign.pub`), PQC y SHA256
   antes de publicar.
7. **SBOM** — generar el Software Bill of Materials (SPDX).
8. **Publicar** — subir artefactos + firmas + SBOM a GitHub Releases.
9. **Re-firmar feed** — si hay feed de actualización, firmarlo con minisign.
10. **Tag git** — `git tag -s` (PGP) y push.
11. **Limpieza** — borrar temporales.

## Verificación por el usuario (offline)

```bash
# minisign
minisign -Vm <artifact>.tar.gz -p minisign.pub

# PQC (con la clave pública embebida en el binario)
<product> verify <artifact>.tar.gz
```

## Rotación de claves

1. Generar nueva clave (`minisign -G`).
2. Firmar la nueva clave pública con la clave actual.
3. Anunciar en el feed (`next_pubkey`) si existe.
4. Esperar un ciclo de actualización para que los clientes persistan la nueva clave.
5. Rotar la clave de firma a partir del siguiente release y actualizar
   `minisign.pub` + la clave embebida.

## Patrones obligatorios

```bash
# ✅ Firmar
minisign -S -m <artifact>.tar.gz -s ~/.minisign/<product>.key

# ✅ Verificar
minisign -Vm <artifact>.tar.gz -p minisign.pub
```

## Anti-patrones prohibidos

```bash
# ❌ Commitear claves privadas o copiarlas a la nube
# ❌ Publicar sin verificar localmente las firmas
# ❌ Firmar con una build que filtra rutas personales (/home/<user>)
```

## Cross-references
- Para la ceremonia completa del proyecto de referencia → ver `docs/en/signing.md` / `docs/es/signing.md`
- Para la licencia y terceros → ver `license/SKILL.md`
