<!-- >>> startai:if-ai-private >>>
# Project Brain (privado)
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
# Project Brain
<!-- <<< startai:endif <<<

Conocimiento compartido entre herramientas de IA. **Agnóstico al editor/IA** —
no contiene nada específico de Windsurf, Copilot, Cursor, Devin, etc.

## Estructura

### Estándar abierto (leído por cualquier IA)

- `AGENTS.md` (raíz) — reglas generales + índice de skills. Estándar `agents.md`.
- `**/AGENTS.md` (anidados) — reglas específicas de directorio (solo los que
  realmente lo necesiten).
- `.agents/skills/*/SKILL.md` — habilidades por dominio. Estándar `agentskills.io`.
- `.agents/agents/*.md` — roles de agente (quién hace qué).
- `.agents/orchestrator/` — contrato opcional para un orquestador de agentes
  externo: `config.yaml`, `roles/`, `workflows/`, `memory/`, `state/`.

### Skills disponibles (10)

| Skill | Dominio |
|-------|---------|
| `ai-native` | Convertir un proyecto en AI-native: AGENTS.md, skills, llms, split público/privado |
| `architecture` | Directrices de ingeniería agnósticas: hexagonal, SOLID, errores tipados, tests |
| `distribution` | Preparar distribución: README bilingüe, GIF, badges, About, social preview |
| `docs-update` | Protocolo de actualización de docs: cabeceras, DOC-SYNC, EN/ES, `[PENDIENTE]` |
| `github-pages` | Sitio estático bilingüe EN/ES, estilo, switcher de idioma, link-check |
| `license` | Licencia propietaria de código visible + licencias de terceros |
| `release` | Pipeline de release: semver, auditoría strict, feed firmado, tag, `gh release` |
| `security` | Anti-filtración, secretos, split público/privado, auditoría como barrera |
| `signing` | Firma minisign (Ed25519) + ML-DSA-65, ceremonia y rotación |
| `updates` | Feed de actualizaciones firmado con minisign; se re-firma en cada release |

Cada `SKILL.md` es autocontenido (no requiere leer otros archivos).

### Roles de agente (`.agents/agents/`)

| Rol | Responsabilidad |
|-----|-----------------|
| `developer.md` | Implementar cambios siguiendo reglas y skills |
| `reviewer.md` | Revisar consistencia EN/ES, placeholders, split público/privado |

## Regla de oro

`AGENTS.md` (raíz + anidados) y `SKILL.md` son el **único lugar donde viven las
reglas y lecciones**. Los demás archivos referencian a ellos o contienen
información complementaria. Nunca copian.

## Público vs privado

<!-- >>> startai:if-ai-private >>>
- **Privado (gitignored):** `**/AGENTS.md`, `.agents/`, `CLAUDE.md`, `.claude/`,
  notas/planes personales, herramientas de dev.
- **Público (versionado):** `llms.txt`, `llms-full.txt`, `docs/`, `README*.md`,
  `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `feed/` (si
  existe — el índice firmado y su `.minisig` son públicos; la clave privada
  `feed/minisign.key` jamás).
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
- **Contexto IA versionado:** `**/AGENTS.md`, `.agents/`, `CLAUDE.md`,
  `.claude/` (visibilidad gobernada por `ai_files_visibility`).
- **Privado (gitignored):** notas/planes personales, herramientas de dev,
  secretos e ignore-files de agente.
- **Público (versionado):** `llms.txt`, `llms-full.txt`, `docs/`, `README*.md`,
  `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `feed/` (si
  existe — el índice firmado y su `.minisig` son públicos; la clave privada
  `feed/minisign.key` jamás).
<!-- <<< startai:endif <<<
