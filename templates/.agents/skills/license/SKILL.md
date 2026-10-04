---
name: license
description: Source-visible proprietary license (template), license coherence checks, third-party license notices generation and audit
---

# License

## Cuándo usar esta skill
- Aplicar la licencia propietaria de código visible a un proyecto.
- Verificar los placeholders de la plantilla (`{{ product_name }}`, `{{ owner }}`, `{{ email }}`, `{{ year }}` — escritos con espacio aquí para que esta skill no se autoprocese; los reales no llevan espacios).
- Generar o mantener el aviso de licencias de terceros.
- Auditar coherencia de licencias (proyecto propietario vs dependencias copyleft).

## Modelo de licencia: "source-visible proprietary"

- **Código visible**: el código se publica en un repo público para que cualquiera
  lo lea, audite y compile.
- **Propietario**: no es open-source. No se permite uso comercial, redistribución,
  obras derivadas ni productos competidores.
- **Divulgación coordinada**: las vulnerabilidades se reportan en privado
  (obligación legal en §5 de la licencia).

La licencia es **bilingüe** (EN + ES) y vive en `LICENSE` (raíz).

## Placeholders de LICENSE

| Placeholder | Valor |
|-------------|-------|
| `{{ product_name }}` | Nombre del software |
| `{{ owner }}` | Titular del copyright (persona o empresa) |
| `{{ email }}` | Contacto para reportes de seguridad y asuntos de licencia |
| `{{ year }}` | Año(s) de publicación |

El generador del scaffold los sustituye automáticamente desde
`config.json` al crear el proyecto. Solo si se copia `templates/LICENSE` a mano
hay que sustituirlos manualmente (ver "Patrones obligatorios").

> No eliminar la cláusula de divulgación coordinada ni los avisos de integridad.

> **Convención de escritura:** en documentos que el generador procesa (templates/
> y las guías copiadas), una referencia ilustrativa a un placeholder se escribe
> con espacio dentro de las llaves (`{{ clave }}`), porque la forma real sin
> espacios sería sustituida por `render()` y marcada por `check.py`.

## Licencias de terceros

- El aviso vive en `THIRD_PARTY_LICENSES.md` (guía) → artefacto generado
  `THIRD_PARTY_LICENSES.txt`.
- Generar **desde el lockfile** con la herramienta del ecosistema (cargo-about,
  license-checker, pip-licenses, license-maven-plugin, go-licenses…).
- Auditar incompatibilidades: una dependencia copyleft (GPL/AGPL) en un proyecto
  propietario requiere evaluación (reemplazo o segregación).

## Checks de coherencia (antes de publicar)

- [ ] `LICENSE` sin placeholders sin sustituir (salvo que sea la plantilla).
- [ ] Nombre del software coherente en LICENSE, README, docs y `llms.txt`.
- [ ] `THIRD_PARTY_LICENSES.txt` regenerado y versionado.
- [ ] `CONTRIBUTING.md` aclara que no se aceptan contribuciones de código.

## Patrones obligatorios

```bash
# ✅ Sustituir placeholders (solo si se copia templates/LICENSE a mano).
#    Los tokens reales no llevan espacios; se construyen con O/C para que
#    este fichero siga siendo renderizable por el generador.
O='{{'; C='}}'
sed -i "s/${O}product_name${C}/Acme Widget/g; s/${O}owner${C}/Acme Corp/g; s/${O}email${C}/legal@example.com/g; s/${O}year${C}/2025/g" LICENSE

# ✅ Generar aviso de terceros (Rust)
cargo about generate about.hbs > THIRD_PARTY_LICENSES.txt
```

## Anti-patrones prohibidos

```bash
# ❌ Publicar código con dependencias copyleft sin declarar
# ❌ Mezclar la licencia del proyecto con el aviso de terceros en un solo fichero
# ❌ Eliminar la cláusula de divulgación coordinada
```

## Cross-references
- Para firmar los artefactos → ver `signing/SKILL.md`
- Para el apartado legal en docs → ver `docs/en/license.md` y `docs/es/license.md`
