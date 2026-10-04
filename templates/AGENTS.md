# AGENTS.md — Reglas universales para agentes IA en `{{product_name}}`

> **Lee primero, edita después.** Este archivo es el **punto de entrada canónico**
> para CUALQUIER agente IA que trabaje en este repositorio:
> GitHub Copilot · Cursor · Claude Code · Codex · Cline · Devin · Windsurf · Aider · etc.
>
> Aquí viven las **reglas mínimas comunes (invariantes)**. El detalle (el "cómo")
> vive en skills autocontenidas bajo `.agents/skills/`. Ver §6 para el índice.

---

## 0. Identidad del repositorio

- **Producto**: `{{product_name}}` — {{description}}
- **Lenguaje/stack**: `{{language}}`.
- **Arquitectura**: {{architecture}}.
- **Repo público**: NUNCA incluir credenciales, secretos ni información privada
  del operador/servidor.

## 1. Inicio de sesión del agente

0. (Recomendado) `bash scripts/dev/session_start.sh` — genera el snapshot de
   sesión (estado de git, tests, docs pendientes) en `/tmp/<repo>_session_context.md`.
1. Leer `AGENTS.md` (este archivo).
2. Leer la skill relevante de la tabla de §6 según el dominio.
3. Leer el rol de agente correspondiente en `.agents/agents/` si existe.

## 2. Regla de oro (única fuente de verdad)

`AGENTS.md` (raíz + anidados) y `SKILL.md` son el **único lugar donde viven las
reglas y lecciones**. Los demás archivos referencian a ellos, nunca copian.

## 3. Reglas operativas mínimas

| Tema | Regla mínima | Skill |
|------|--------------|-------|
| Arquitectura | Hexagonal/SOLID como referencia; la variante concreta va en {{architecture}}. | `architecture` |
| Documentación bilingüe | README + sitio estático en EN **y** ES. | `github-pages` |
| Actualización de docs | Tras cada tarea: cabecera (Versión/Fecha), DOC-SYNC, sin `[PENDIENTE]`. | `docs-update` |
| Licencias | No añadir dependencias sin registrar su licencia. | `license` |
| Firmas | Todo release se firma minisign **y** ML-DSA-65. | `signing` |
| Actualizaciones | Feed firmado de actualizaciones: re-firmar `feed/advisories.json` en cada release; `feed/minisign.key` nunca versionada. | `updates` |
| Secretos | Nunca commitear secretos (`*.key`, `*.pem`, `.env*`). | `ai-native` |
| Anti-filtración | Repo público: credenciales, secretos y datos privados jamás en ficheros versionados; barreras = hook `pre-commit` + auditoría `--strict`. | `security` |
| Release | `scripts/dev/release.sh` orquesta auditoría, bump, feed, tag y `gh release`. | `release` |

**Control de cambios:** prohibido modificar código o docs existentes sin
autorización explícita — proponer plan → confirmar → aplicar (excepción:
corregir errores introducidos por el propio agente). Trabajo pendiente en
código o ficheros privados: `TODO[ID]: Título | Descripción | Estado |
Responsable | Fecha | Prioridad`.

## 4. Split público / privado

<!-- >>> startai:if-ai-private >>>
- **Privado (gitignored):** `**/AGENTS.md`, `.agents/`, `CLAUDE.md`, `.claude/`,
  notas/planes personales, herramientas de dev, secretos.
- **`.devinignore`:** des-ignora lo privado **solo para las tools del agente**.
  Git no lo lee. **Nunca** negar secretos ni artefactos.
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
- **Contexto IA versionado (público):** `**/AGENTS.md`, `.agents/`,
  `CLAUDE.md`, `.claude/` — `ai_files_visibility="public"` en `config.json`.
- **Privado (gitignored):** notas/planes personales, herramientas de dev,
  secretos e ignore-files de agente (`.devinignore` y afines — des-ignoran
  lo privado solo para las tools; nunca secretos ni artefactos).
<!-- <<< startai:endif <<<

## 5. Checklist mínimo antes de declarar una tarea hecha

- [ ] Build/tests pasan.
- [ ] Reglas nuevas → añadidas a la skill correspondiente.
- [ ] Documentación pública actualizada (EN/ES si aplica).
- [ ] Commit sin secretos ni rutas privadas.

## 6. Workflow + índice de skills

### Skills disponibles (`.agents/skills/`)

| Skill | Path | Aplicar cuando |
|-------|------|---------------|
| `ai-native` | `.agents/skills/ai-native/SKILL.md` | Convertir un proyecto en AI-native |
| `architecture` | `.agents/skills/architecture/SKILL.md` | Crear/modificar código: hexagonal, SOLID, errores, tests |
| `distribution` | `.agents/skills/distribution/SKILL.md` | Preparar distribución (README, GIF, About) |
| `docs-update` | `.agents/skills/docs-update/SKILL.md` | Mantener docs sincronizados tras cada cambio (DOC-SYNC, cabeceras, EN/ES) |
| `github-pages` | `.agents/skills/github-pages/SKILL.md` | Sitio estático bilingüe EN/ES |
| `license` | `.agents/skills/license/SKILL.md` | Licencia propietaria + terceros |
| `release` | `.agents/skills/release/SKILL.md` | Pipeline de release: semver, auditoría, feed, tag, `gh release` |
| `security` | `.agents/skills/security/SKILL.md` | Anti-filtración, secretos, split público/privado, auditoría |
| `signing` | `.agents/skills/signing/SKILL.md` | Firma minisign + ML-DSA-65 |
| `updates` | `.agents/skills/updates/SKILL.md` | Feed de actualizaciones firmado con minisign: esquema, firma, publicación |

### Roles de agente (`.agents/agents/`)

| Rol | Path | Responsabilidad |
|-----|------|-----------------|
| `developer` | `.agents/agents/developer.md` | Implementar cambios siguiendo reglas y skills |
| `reviewer` | `.agents/agents/reviewer.md` | Revisar consistencia, placeholders, split público/privado |

## 7. Tooling del proyecto y hooks de git

- **Coherencia del scaffold**: `python3 scripts/check.py` — config sin valores
  vacíos, sin placeholders sin resolver, paridad de docs EN/ES.
- **Publicación en GitHub** (sin navegador): `python3 scripts/github.py`
  subcomandos `create` / `pages` / `status` (requiere `gh` autenticado).
- **Hooks** (`scripts/git/`): `pre-commit` (check + anti-secretos + rutas
  privadas), `commit-msg` (rechaza atribución IA), `pre-push` (tests +
  auditoría `--strict`); términos privados: `scripts/dev/forbidden-terms.conf`
  (gitignored, nunca en los hooks). Instalar: `bash scripts/git/install-hooks.sh`.
- **Auditoría de desarrollo** (`scripts/dev/audit/`, privada):
  `bash scripts/dev/audit/run_all.sh --profile project [--strict]` — checks de
  secretos, enlaces, docs, rutas privadas y versión. Contrato y exit codes en
  `scripts/dev/audit/README.md`.
- **Versión del producto** (`scripts/dev/`, privada): la fuente canónica es
  `CHANGELOG.md` (primer `## [x.y.z]`). `bash scripts/dev/sync_version.sh`
  propaga a los `VERSION_TARGETS` del perfil de auditoría; `--check` solo
  verifica; `--bump X.Y.Z` convierte `[Unreleased]` en la entrada fechada y
  propaga; `--release-feed` actualiza `latest`/`published_at` de
  `feed/advisories.json` y lo re-firma con `feed/minisign.key`. Las cabeceras
  `Versión:`/`Version:` de docs y AGENTS.md son de DOCUMENTO — no se tocan.
- **Release** (`scripts/dev/`, privada): `bash scripts/dev/release.sh
  [--bump X.Y.Z] [--dry-run] [--yes] [--allow-unsigned]` — auditoría strict,
  sync de versión, feed, tag (PGP si disponible), tarball + sha256 +
  minisign (bloqueante), y `gh release create` con notas del CHANGELOG.

---

**Versión**: 1.1 (`{{year}}`)
