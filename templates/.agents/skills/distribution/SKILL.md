---
name: distribution
description: Prepare a project for distribution: bilingual README, demo GIF, shields.io badges, GitHub About section, social preview, visibility and promotion
---

# Distribution

## Cuándo usar esta skill
- Dejar un proyecto listo para publicarse/distribuirse en un repositorio
  (GitHub o similar).
- Crear/actualizar README bilingüe, GIF de demo, badges, apartado "About",
  imagen de social preview, o configurar visibilidad y promoción.

## Proceso (paso a paso)

### 1. README bilingüe (EN/ES)
- `README.md` (EN) y `README.es.md` (ES), enlazados entre sí en la cabecera.
- Estructura estándar: título + badges → GIF de demo → pitch de una línea →
  características → arquitectura → tabla de contenidos → instalación → uso →
  documentación → licencia.
- Badges con shields.io: versión, licencia, plataforma, lenguaje.

### 2. GIF de demostración
- Grabar sesión de terminal con `asciinema` (genera `.cast`).
- Renderizar a `.gif` (p. ej. `agg`, `ttygif`, `vhs`).
- Committear `.gif` (y el `.cast` + script que lo genera) bajo `docs/`.
- Referenciarlo en el README y en la home del sitio estático.
- **Mientras no exista `docs/demo.gif`**, el README lo lleva comentado en un
  bloque `<!-- ... -->` (no meter la imagen rota). Tras grabarlo, descomentar
  esa línea en `README.md` y `README.es.md`.

### 3. Apartado "About" del repositorio (GitHub)
- **Description**: una frase con palabras clave.
- **Website**: la URL del sitio GitHub Pages (`https://<owner>.github.io/<repo>/`).
- **Topics**: etiquetas de descubrimiento (lenguaje, dominio, "cli", "tor", etc.).

### 4. Sitio estático (GitHub Pages)
- Publicar desde `docs/` (Jekyll). Ver `github-pages/SKILL.md`.

### 5. Social preview / Open Graph
- Imagen 1280×640 (`docs/assets/social-preview.svg`), subir como PNG en
  Settings → Social preview.

### 6. Visibilidad y promoción
- Repo público (o source-visible) según el modelo de licencia.
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.
- Releases firmados (ver `signing/SKILL.md`) + `llms.txt` para IA.

## Patrones obligatorios

```bash
# ✅ Badges
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary%20(source--visible)-orange.svg)

# ✅ Grabar y renderizar demo
asciinema rec docs/demo.cast
agg docs/demo.cast docs/demo.gif
```

## Anti-patrones prohibidos

```bash
# ❌ README solo en un idioma (rompe la promesa bilingüe)
# ❌ GIF de demo con secretos o rutas personales visibles
# ❌ "About" sin website ni topics (pierde descubrimiento)
# ❌ Social preview sin configurar (tarjeta por defecto de GitHub)
```

## Cross-references
- Para el sitio estático → ver `github-pages/SKILL.md`
- Para la licencia → ver `license/SKILL.md`
- Para firmar releases → ver `signing/SKILL.md`
