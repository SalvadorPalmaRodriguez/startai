---
layout: default
title: Licencias
lang: es
---
> **Documento de usuario:** `docs/es/license.md`
> **Versión:** 1.1 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** LICENSE · THIRD_PARTY_LICENSES.md

# Licencias

La licencia que tu proyecto entrega es **propietaria de código visible**: tu
código sigue visible en el repositorio, pero privado y no redistribuible.

---

## La licencia

El fichero `LICENSE` es una **plantilla** (inglés + español) que usa los mismos
placeholders de doble llave que el resto del kit:

| Placeholder | Valor |
|-------------|-------|
| `{{ product_name }}` | Nombre del software |
| `{{ owner }}` | Titular del copyright (persona o empresa) |
| `{{ email }}` | Contacto para reportes de seguridad y asuntos de licencia |
| `{{ year }}` | Año(s) de publicación |

Al generar el proyecto, el generador sustituye los cuatro automáticamente
desde `config.json` — no hace falta ningún paso manual.
(Aquí se escriben como `{{ key }}` — con espacio — para que este propio
documento no sea reescrito durante la generación; los placeholders reales no
llevan espacios.)

Si en cambio copias `templates/LICENSE` a mano, ejecuta:

```bash
# Los tokens reales no llevan espacios; se construyen aquí para que este
# documento siga siendo renderizable (un token literal sería sustituido por
# el generador).
O='{{'; C='}}'
sed -i "s/${O}product_name${C}/Acme Widget/g; s/${O}owner${C}/Acme Corp/g; s/${O}email${C}/legal@example.com/g; s/${O}year${C}/2025/g" LICENSE
```

No elimines la cláusula de divulgación coordinada (§5) ni los avisos de
integridad.

## Qué concede y qué restringe la licencia

- **Concede** — ver, leer y compilar el código para uso personal no comercial;
  copias de seguridad.
- **Restringe** — uso comercial, redistribución, obras derivadas, productos
  competidores, eliminación de avisos.
- **Obliga** — las vulnerabilidades se reportan en privado en 72 horas
  (divulgación coordinada).

## Licencias de terceros

Las dependencias conservan sus licencias y deben listarse. Genera el aviso desde
el lockfile con la herramienta del ecosistema:

| Ecosistema | Herramienta |
|------------|-------------|
| Rust / Cargo | `cargo-about`, `cargo-deny` |
| Node / npm | `license-checker`, `npm-license-crawler` |
| Python | `pip-licenses` |
| Java / Maven | `license-maven-plugin` |
| Go | `go-licenses` |

Mantén el aviso en `THIRD_PARTY_LICENSES.md` (guía) → fichero generado
`THIRD_PARTY_LICENSES.txt`. Audita incompatibilidades copyleft (GPL/AGPL) con un
proyecto propietario.

---

Ver también: [Preparar un proyecto para distribución](distribution.md) · [Firma de releases](signing.md).
