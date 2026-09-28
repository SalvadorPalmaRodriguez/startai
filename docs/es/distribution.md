---
layout: default
title: Preparar un proyecto para distribución
lang: es
---
> **Documento de usuario:** `docs/es/distribution.md`
> **Versión:** 1.1 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** README.md · skill `distribution`

# Preparar un proyecto para distribución

Cómo dejar un proyecto listo para su distribución en un repositorio, con los
mismos apartados de visibilidad y promoción que un repo público cuidado.

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

## 2. GIF de demostración

Graba una sesión de terminal y renderízala a GIF:

```bash
asciinema rec docs/demo.cast      # grabar
agg docs/demo.cast docs/demo.gif  # renderizar a GIF
```

Commitea el `.gif` (además del `.cast` y el script que lo genera) bajo `docs/`.
Referéncialo desde el README y la home del sitio estático.

## 3. Apartado "About" del repositorio (GitHub)

En la configuración del repositorio (About), establece:

- **Description** — una frase con palabras clave.
- **Website** — la URL de GitHub Pages: `https://<owner>.github.io/<repo>/`.
- **Topics** — etiquetas de descubrimiento (lenguaje, dominio, `cli`, `docs`…).

## 4. Sitio estático (GitHub Pages)

Publica desde `docs/` con Jekyll (ver la skill `github-pages`).
Ajusta: Settings → Pages → Source → Deploy from branch → `/docs`.

## 5. Social preview / Open Graph

Crea una imagen 1280×640 (`docs/assets/social-preview.svg`) y súbela como PNG en
Settings → Social preview, para que los enlaces muestren una tarjeta cuidada.

## 6. Visibilidad y promoción

- Repositorio público (código visible).
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.
- Releases firmados (ver [Firma de releases](signing.md)) y `llms.txt` para IA.

---

Ver también: [Convertir un proyecto en AI-native](ai-native.md) · [Licencias](license.md).
