---
layout: default
title: Convertir un proyecto en AI-native
lang: es
---
> **Documento de usuario:** `docs/es/ai-native.md`
> **Versión:** 1.3 | **Actualizado:** 2026-09-28
> **Estado:** ✅ **VIGENTE**
> **Referencias:** distribution.md

# Convertir un proyecto en AI-native

Esta guía convierte tu proyecto en uno donde un agente IA puede trabajar de
forma nativa y consistente. La idea clave: **tus reglas viven en un solo
sitio, y los agentes las descubren mediante ficheros estándar.**

---

## 1. `AGENTS.md` en la raíz

Es el **punto de entrada canónico** para cualquier agente IA (Copilot, Cursor,
Claude Code, Codex, Cline, Devin, Windsurf, Aider…). Contiene:

- **Identidad** — qué es el proyecto, su lenguaje y arquitectura.
- **Invariantes** — las reglas mínimas que todo agente debe respetar.
- **Tabla regla → skill** — cada tema enlaza a la skill con el detalle.
- **Índice de skills** — la lista de `.agents/skills/*`.

```markdown
# AGENTS.md — reglas universales para agentes IA

> Lee primero, edita después. Punto de entrada canónico para CUALQUIER agente IA.

## Reglas
| Tema | Regla mínima | Skill |
|------|--------------|-------|
| Commits | Firmar con `git commit -S` | security |
```

## 2. `AGENTS.md` anidados (solo donde haga falta)

Añadir `**/AGENTS.md` **solo** en directorios con reglas específicas. Nunca
duplicar el índice de la raíz; el anidado referencia la raíz y añade lo local.

## 3. `.agents/skills/<name>/SKILL.md`

Skills de dominio autocontenidas (estándar `agentskills.io`). Cada una empieza
con frontmatter para que las herramientas la descubran por su `description`:

```markdown
---
name: security
description: commits PGP, secretos, auditoría, divulgación coordinada
---

# Security
## Cuándo usar esta skill
...
```

**Regla de oro:** `AGENTS.md` + `SKILL.md` son el único hogar de reglas y
lecciones. Lo demás referencia, nunca copia.

## 4. `.agents/agents/<name>.md`

Roles de agente — "quién hace qué" (developer, reviewer, security…). Separar el
*rol* (persona) de la *skill* (capacidad de dominio).

## 5. `.agents/README.md`

El "Project Brain": explica la estructura, la regla de oro y qué es público
vs privado.

## 6. `llms.txt` y `llms-full.txt`

Contexto IA público y versionado:

- `llms.txt` — índice breve para crawlers: qué es el proyecto, notas legales,
  enlaces a la documentación.
- `llms-full.txt` — contexto expandido en un solo fichero.

Incluir siempre: *"La legibilidad por IA no constituye concesión de licencia."*

## 7. Split público / privado

- **`.gitignore`** — ignorar `**/AGENTS.md`, `.agents/`, `CLAUDE.md`, `.claude/`,
  notas/planes personales, herramientas de dev y secretos.
- **`.devinignore`** — fichero gitignored con negaciones `!` que des-ignoran lo
  privado **solo para las tools del agente** (read/edit/grep). Git no lo lee,
  así que nada privado se stagea. **Nunca** negar secretos ni artefactos.

## 8. Opcional: bridge y orquestador

- `CLAUDE.md` con `@AGENTS.md` para Claude Code.
- Un orquestador custom (`roles/`, `workflows/`, `memory/`, `state/`) si el
  equipo usa un dev-agent orquestador.

## 9. Adoptar en un proyecto existente

Cuando el proyecto ya existe, el kit se aplica **por capas** en lugar de
generar desde cero. El flujo de adopción:

1. **Preflight primero**: inspecciona el repo buscando lo que rompería
   después — tokens de plantilla (`{{ x }}`/`{ALL-CAPS}`) que el chequeo de
   coherencia rechazaría en cada commit, rutas privadas ya trackeadas por
   git, hooks de git preexistentes, generadores de docs en conflicto, falta
   de paridad bilingüe.
2. **Aplicar por capas**: `agents` (contexto IA) → `hooks` → `audit` →
   `docs` → `distribution` → `release`. Los ficheros en conflicto nunca se
   sobrescriben; se desvían a `<ruta>.startai-new` para merge manual.
3. **El enforcement es opt-in**: los hooks de git se entregan pero nunca se
   instalan automáticamente; las entradas del perfil de auditoría para
   ficheros que aún no existen se comentan, no se borran.
4. **Split privado aditivo**: `.gitignore` recibe siempre un bloque
   gestionado marcado e idempotente (el manifiesto de adopción debe quedar
   ignorado); `.devinignore` lo recibe solo con la capa `agents` — las
   líneas del usuario no se tocan.
5. **Manifiesto**: un `.startai-adopt.json` registra capas adoptadas y
   hashes de ficheros, así que re-ejecutar la adopción es idempotente y puede
   actualizar ficheros del kit sin tocar los que el usuario editó.

Un checklist manual es una vía igualmente soportada cuando prefieres
control total — pero es de dos fases: los ficheros del kit se renderizan
primero en un directorio de staging (nunca se copian directamente desde
`templates/`, que lleva placeholders sin resolver), luego se copian al
proyecto, y el bloque marcado de `.gitignore` se añade para que el
manifiesto de adopción quede privado. Añadirlo a mano no es idempotente: en
una adopción manual repetida, borra primero el bloque marcado anterior para
no acabar con dos.

---

Ver también: [Preparar un proyecto para distribución](distribution.md) · [Licencias](license.md).
