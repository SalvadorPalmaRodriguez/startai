---
name: github-pages
description: GitHub Pages static site, bilingual docs EN/ES, hacker CSS style, Jekyll _config.yml with theme null, custom layout with language switcher, social preview, link-checker
---

# GitHub Pages

## Cuándo usar esta skill
- Crear o mantener el sitio estático servido por GitHub Pages (Jekyll desde `docs/`).
- Añadir o traducir páginas EN/ES.
- Cambiar el estilo visual del sitio.
- Configurar la imagen de social preview.

## Reglas

### Estilo
- El CSS vive en `docs/assets/hacker.css` (un solo fichero). Cualquier cambio
  visual se hace ahí, no en páginas individuales.
- El layout Jekyll (`docs/_layouts/default.html`) aplica el CSS a todas las páginas.

### Bilingüe (EN/ES)
- Páginas EN: `docs/index.md` (home) + `docs/en/*.md`.
- Páginas ES: `docs/es/index.md` + `docs/es/*.md`.
- El layout incluye un switcher de banderas (🇪🇸 🇺🇸) que mapea cada página vía
  Liquid `case` (bidireccional).
- Al añadir una página traducida, actualizar el `case` en `default.html` con el
  mapeo bidireccional.

### Jekyll config
- `theme: null` (sin tema externo). El layout custom es el único punto de entrada.
- `_config.yml` en la raíz de `docs/`.

### Logo y social preview
- Logo: `docs/assets/logo.svg`.
- Social preview: `docs/assets/social-preview.svg` (1280×640). Subir manualmente
  como PNG en GitHub Settings → Social preview.

### Cabecera del documento — actualizar al modificarlo
Todo documento de `docs/` lleva cabecera de metadatos:

| Campo | Regla |
|-------|-------|
| `**Versión:**` / `**Version:**` | Incrementar: patch si corriges, minor si añades. |
| `**Actualizado:**` / `**Updated:**` | Fecha de hoy (`YYYY-MM-DD`). |
| `**Estado:**` / `**Status:**` | `VIGENTE`/`CURRENT`, `HISTÓRICO`, `DEPRECATED`, `BORRADOR`. |
| `**Referencias:**` / `**References:**` | Docs relacionados. |

### Link-checker
- Antes de commitear, verificar que los enlaces entre páginas y los fragmentos
  `#ancla` son válidos (script propio `04_web_links.sh` o `lychee`).

### Cuándo actualizar Pages
- Push a `main` dispara el build automático.
- Si no dispara: `gh api repos/<owner>/<repo>/pages/builds -X POST`.
- Verificar: `gh api repos/<owner>/<repo>/pages/builds --jq '.[0].status'`.
- Caché del navegador: `Ctrl+Shift+R`.

## Patrones obligatorios

```bash
# ✅ Verificar build de Pages
gh api repos/<owner>/<repo>/pages/builds --jq '.[0].status'

# ✅ Publicar desde docs/ — settings: Pages → Source → Deploy from branch → /docs
```

## Anti-patrones prohibidos

```bash
# ❌ CSS inline en páginas individuales
# ❌ Añadir página sin actualizar el case en default.html
# ❌ Theme externo (cayman) en _config.yml
```

## Cross-references
- Para README/GIF/About → ver `distribution/SKILL.md`
- Para DOC-SYNC tras cambios de código → ver `ai-native/SKILL.md`
