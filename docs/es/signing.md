---
layout: default
title: Firma de releases
lang: es
---
> **Documento de usuario:** `docs/es/signing.md`
> **Versión:** 1.4 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** license.md · distribution.md

# Firma de releases

El kit establece un modelo de doble firma para los releases — una capa
clásica y una post-cuántica — para que los usuarios puedan verificar una
descarga **offline**:

| Capa | Algoritmo | Clave pública | Fichero de firma |
|------|-----------|---------------|------------------|
| Clásica | Ed25519 (minisign) | `minisign.pub` (raíz repo) | `<artifact>.tar.gz.minisig` |
| Post-cuántica | ML-DSA-65 (FIPS 204) | `pqc_sign.pub` (raíz repo) | `<artifact>.tar.gz.pqsig` |

## Verificar una descarga (offline)

```bash
# minisign (Ed25519)
minisign -Vm <artifact>.tar.gz -p minisign.pub

# ML-DSA-65: verificar <artifact>.tar.gz.pqsig contra pqc_sign.pub
#   con cualquier verificador ML-DSA-65
```

Para proyectos que distribuyen un CLI, embeber la clave pública en el binario
y exponer un subcomando de verificación (`<product> verify <artifact>.tar.gz`)
es una comodidad opcional — la verificación genérica `.pqsig` + `pqc_sign.pub`
siempre funciona.

---

Ver también: [Licencias](license.md) · [Preparar un proyecto para distribución](distribution.md).
