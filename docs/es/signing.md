---
layout: default
title: Firma de releases
lang: es
---
> **Documento de usuario:** `docs/es/signing.md`
> **Versión:** 1.5 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** license.md · distribution.md

# Firma de releases

Cada release que publiques lleva **dos firmas** — una clásica y una
post-cuántica — para que cualquiera pueda verificar tus descargas **sin
conexión**, incluso años después:

| Capa | Algoritmo | Clave pública | Fichero de firma |
|------|-----------|---------------|------------------|
| Clásica | Ed25519 (minisign) | `minisign.pub` (raíz repo) | `<artifact>.tar.gz.minisig` |
| Post-cuántica | ML-DSA-65 (FIPS 204) | `pqc_sign.pub` (raíz repo) | `<artifact>.tar.gz.pqsig` |

## Cómo verifican tus usuarios una descarga (sin conexión)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# ML-DSA-65: verificar <artifact>.tar.gz.pqsig contra pqc_sign.pub
#   con cualquier verificador ML-DSA-65
```

Si tu proyecto distribuye un CLI, también puedes embeber la clave pública en
el binario y ofrecer un subcomando de verificación (`<product> verify
<artifact>.tar.gz`) — una comodidad opcional; la verificación genérica
`.pqsig` + `pqc_sign.pub` siempre funciona.

---

Ver también: [Licencias](license.md) · [Preparar un proyecto para distribución](distribution.md).
