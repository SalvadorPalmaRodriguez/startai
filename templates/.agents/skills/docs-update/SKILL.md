---
name: docs-update
description: Documentation update protocol — after every code change, bump doc headers (Version, Updated), keep EN/ES in sync, apply DOC-SYNC for new config sources, and remove [PENDIENTE] markers
---

# Actualización de documentación (DOC-SYNC)

## Cuándo usar esta skill
- Tras **cualquier** tarea de código o configuración, antes de declararla hecha.
- Al añadir una fuente de configuración (flag, env var, fichero de config).
- Cuando un doc queda desfasado respecto al código.

## Reglas

### Regla global (obligatoria tras cada tarea)
Actualizar los documentos afectados **antes del commit**. Una tarea no está
terminada si el código dice una cosa y la documentación otra.

### Cabecera de cada documento modificado
Cada doc público lleva cabecera y debe mantenerse:

```
> **Versión:** X.Y | **Actualizado:** YYYY-MM-DD   (documentos en español)
> **Version:** X.Y  | **Updated:** YYYY-MM-DD      (documentos en inglés)
```

- **Versión**: se incrementa al modificar el documento. Es la versión **del
  documento**, no la del producto — no tienen por qué coincidir.
- **Actualizado/Updated**: fecha de hoy, formato `YYYY-MM-DD`.
- Si el documento tiene `Estado`/`Status` y `Referencias`, mantenerlos.
  La línea `Referencias`/`References` solo admite rutas **públicas**; las
  skills se citan por nombre, nunca por ruta privada (check 24).
- La auditoría (`scripts/dev/audit/`, check `05_docs_crossref`) verifica el
  formato de estas cabeceras — respetarlo exactamente.

### DOC-SYNC: nuevas fuentes de configuración
Cada vez que se añade una fuente de configuración (flag CLI, variable de
entorno, clave de fichero de config):
1. Actualizar el fichero de ejemplo del proyecto.
2. Actualizar `llms.txt` / `llms-full.txt`.
3. Si es visible para el usuario, actualizar el README (EN y ES).

### Marcadores `[PENDIENTE]`
- Úsalos para marcar trabajo consciente pendiente.
- **Elimínalos** cuando el código esté implementado — un `[PENDIENTE]` en un
  release es un fallo. El check `17_docs_sync_markers` los detecta.

### Paridad EN/ES
Toda documentación pública existe en inglés y español a la vez. Si tocas una
página en `docs/en/`, toca su contraparte en `docs/es/` con el mismo cambio.

### No crear documentos nuevos
Salvo que la tarea lo requiera. Documentación extra = superficie de
mantenimiento extra.
