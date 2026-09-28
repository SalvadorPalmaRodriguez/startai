---
layout: default
title: Preparar tu proyecto para distribución
lang: es
---
> **Documento de usuario:** `docs/es/distribution.md`
> **Versión:** 1.5 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** README.md · ai-native.md

# Preparar tu proyecto para distribución

Lo que tu proyecto nuevo incluye de serie — y cómo rellenar cada plantilla
con tus propios valores.

---

## 1. README bilingüe (EN/ES)

`README.md` (EN) y `README.es.md` (ES), enlazados entre sí en la cabecera.

Estructura estándar:

```
# {{ product_name }} — {{ tagline }}
**English** · **[Español](README.es.md)**

[badges: versión, licencia, plataforma, lenguaje]
![GIF de demo](docs/demo.gif)

> pitch de una línea + 3 puntos clave + enlace docs + nota llms.txt

## Características
## Arquitectura
## Tabla de Contenidos
## Instalación
## Uso
## Licencia
```

## 2. Lo que incluye tu proyecto

- **Esqueleto de sitio estático bilingüe** — un sitio `docs/` (configuración,
  layout propio con selector de idioma EN/ES, estilos) listo para GitHub Pages.
- **`docs/assets/social-preview.svg`** — plantilla 1280×640 para la tarjeta de
  previsualización de enlaces; edita los textos y expórtala a PNG.
- **Plantillas legales y de comunidad** — `SECURITY.md`, `CONTRIBUTING.md`,
  `CHANGELOG.md` (Keep a Changelog), `LICENSE` y `THIRD_PARTY_LICENSES.md`.
- **`llms.txt` / `llms-full.txt`** — ficheros de contexto para indexadores IA,
  con la nota legal ya incluida.
- Tu repo está pensado para ser público (código visible), y tus releases salen
  con doble firma (ver [Firma de releases](signing.md)).

---

Ver también: [Convertir un proyecto en AI-native](ai-native.md) · [Licencias](license.md).
