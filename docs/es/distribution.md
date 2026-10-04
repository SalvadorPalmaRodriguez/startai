---
layout: default
title: Preparar tu proyecto para distribución
lang: es
---
> **Documento de usuario:** `docs/es/distribution.md`
> **Versión:** 1.7 | **Actualizado:** 2026-10-04
> **Estado:** ✅ **VIGENTE**
> **Referencias:** README.md · ai-native.md

# Preparar tu proyecto para distribución

Lo que tu proyecto nuevo incluye de serie — y cómo rellenar cada plantilla
con tus propios valores.

---

## README bilingüe (EN/ES)

`README.md` (EN) y `README.es.md` (ES), enlazados entre sí en la cabecera.

Estructura estándar (los placeholders van aquí con espacio — `{{ nombre }}` —
para que esta página se renderice; los tokens reales no llevan espacios):

```
# {{ product_name }} — {{ tagline }}
**English** · **[Español](README.es.md)**

[badges: versión, licencia, plataforma, lenguaje]
<!-- graba con `asciinema rec docs/demo.cast` + `agg docs/demo.cast docs/demo.gif`, y luego descomenta:
![GIF de demo](docs/demo.gif)
-->

> pitch de una línea + 3 puntos clave + enlace docs + nota llms.txt

## Características
## Arquitectura
## Tabla de Contenidos
## Instalación
## Uso
## Licencia
```

El GIF de demo viaja comentado a propósito: graba una sesión de terminal con
`asciinema`, renderízala con `agg`, commitea `docs/demo.gif` y luego
descomenta la línea. Configura también el About del repo (description +
homepage + topics) — `python3 scripts/github.py create` lo hace desde
consola.

## Lo que incluye tu proyecto

- **Esqueleto de sitio estático bilingüe** — un sitio `docs/` (configuración,
  layout propio con selector de idioma EN/ES, estilos) listo para GitHub
  Pages. Actívalo con `python3 scripts/github.py pages --owner <usuario>
  --repo <repo>`; previsualiza en local con `bundle exec jekyll serve` dentro
  de `docs/`.
- **Selector de idioma** — los pares de páginas están fijos en el mapa
  `{% raw %}{% case %}{% endraw %}` de `docs/_layouts/default.html`; al añadir una página, añade
  su par EN/ES ahí o el selector caerá al índice del idioma.
- **`docs/assets/social-preview.svg`** — plantilla 1280×640 para la tarjeta de
  previsualización de enlaces; edita los textos y expórtala a PNG.
- **Plantillas legales y de comunidad** — `SECURITY.md`, `CONTRIBUTING.md`,
  `CHANGELOG.md` (Keep a Changelog), `LICENSE` y `THIRD_PARTY_LICENSES.md`.
- **`.github/`** — plantillas públicas de issues (bug, feature, contact links).
- **Feed de actualizaciones firmado** — `feed/` (`advisories.json` + README):
  el índice firmado con minisign que tus usuarios consultan para saber si hay
  versión nueva; `feed/minisign.key` queda privada.
- **Tooling del proyecto** — `scripts/check.py`, `scripts/github.py`, hooks
  `scripts/git/` (opt-in) y un toolkit privado de auditoría y release (fuera
  de git vía el `.gitignore` generado).
- **`llms.txt` / `llms-full.txt`** — ficheros de contexto para indexadores IA,
  con la nota legal ya incluida.
- Tu repo está pensado para ser público (código visible), y tus releases salen
  con doble firma (ver [Firma de releases](signing.md)).

---

Ver también: [Convertir un proyecto en AI-native](ai-native.md) · [Licencias](license.md).
