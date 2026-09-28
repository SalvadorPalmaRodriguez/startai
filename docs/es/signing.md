---
layout: default
title: Firma de releases
lang: es
---
> **Documento de usuario:** `docs/es/signing.md`
> **Versión:** 1.1 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** skill `signing`

# Firma de releases

Cada release se firma dos veces para verificar su autenticidad — incluso offline:

| Capa | Algoritmo | Clave privada | Clave pública |
|------|-----------|---------------|---------------|
| Clásica | Ed25519 (minisign) | `~/.minisign/<product>.key` | `minisign.pub` (raíz repo) |
| Post-cuántica | ML-DSA-65 (FIPS 204) | `~/.<product>/pqc_signing.key` | `pqc_sign.pub` (raíz repo) |

Las claves privadas **nunca se commitean**; viven fuera del repo con permisos
`0600` y passphrase.

---

## Ceremonia de firma

1. **Build reproducible** — compilar con rutas neutras (sin `/home/<user>`).
2. **Empaquetar** — tarball del artefacto.
3. **SHA256** — `sha256sum <artifact>.tar.gz`.
4. **minisign** — `minisign -S -m <artifact>.tar.gz -s ~/.minisign/<product>.key`.
5. **PQC** — firmar con ML-DSA-65 → `<artifact>.tar.gz.pqsig`.
6. **Verificación local** — verificar minisign, PQC y SHA256 antes de publicar.
7. **SBOM** — generar el Software Bill of Materials (SPDX).
8. **Publicar** — subir artefacto + firmas + SBOM a GitHub Releases.
9. **Re-firmar el feed** (si existe) con minisign.
10. **Tag** — `git tag -s` (PGP) y push.
11. **Limpieza** — borrar temporales.

## Verificación por el usuario (offline)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# post-cuántica (ML-DSA-65), clave embebida en el binario
<product> verify <artifact>.tar.gz
```

## Rotación de claves

1. Generar nueva clave (`minisign -G`).
2. Firmar la nueva clave pública con la clave actual.
3. Anunciarla en el feed (`next_pubkey`) si existe.
4. Esperar un ciclo de actualización para que los clientes persistan la nueva clave.
5. Rotar la clave de firma en el siguiente release y actualizar `minisign.pub` +
   la clave embebida.

---

Ver también: [Licencias](license.md) · [Preparar un proyecto para distribución](distribution.md).
