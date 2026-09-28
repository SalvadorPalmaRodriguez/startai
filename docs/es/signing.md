---
layout: default
title: Firma de releases
lang: es
---
> **Documento de usuario:** `docs/es/signing.md`
> **Versión:** 1.3 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** skill `signing`

# Firma de releases

El kit establece un modelo de doble firma para los releases — una capa
clásica y una post-cuántica — para que los usuarios puedan verificar una
descarga **offline**:

| Capa | Algoritmo | Clave privada | Clave pública |
|------|-----------|---------------|---------------|
| Clásica | Ed25519 (minisign) | fuera del repo, `0600` + passphrase | `minisign.pub` (raíz repo) |
| Post-cuántica | ML-DSA-65 (FIPS 204) | fuera del repo, `0600` + passphrase | `pqc_sign.pub` (raíz repo) |

Las claves privadas **nunca se commitean**; viven fuera del repositorio con
permisos `0600` y passphrase.

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

La ceremonia de firma y la rotación de claves son procesos del propietario;
viven en la skill `signing`, no en esta guía pública.

---

Ver también: [Licencias](license.md) · [Preparar un proyecto para distribución](distribution.md).
