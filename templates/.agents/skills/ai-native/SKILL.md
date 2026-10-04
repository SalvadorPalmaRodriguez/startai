---
name: ai-native
description: Convert a normal project into an AI-native project: AGENTS.md, .agents/ agents and skills, llms.txt / llms-full.txt, public/private split with .gitignore and .devinignore
---

# AI-native

## Cuándo usar esta skill
- Convertir un proyecto "normal" en un proyecto donde una IA pueda trabajar de
  forma nativa y consistente.
- Añadir reglas, skills, roles o contexto IA (llms.txt) a un repo existente.
- Configurar el split público/privado para que los agentes lean lo privado sin
  que Git lo versione.

## Proceso (paso a paso)

### 1. `AGENTS.md` en la raíz
- Es el **punto de entrada canónico** para cualquier agente IA.
- Contenido: identidad del repo, reglas mínimas comunes (invariantes), tabla de
  reglas → skill, y un índice de skills (§).
- Estándar: `agents.md`. Mencionar explícitamente las herramientas soportadas
  (Copilot, Cursor, Claude Code, Codex, Cline, Devin, Windsurf, Aider…).

### 2. `AGENTS.md` anidados (solo si hace falta)
- Añadir `**/AGENTS.md` **solo** en directorios con reglas específicas.
- No duplicar: el anidado referencia la raíz y añade solo lo propio.

### 3. `.agents/skills/<name>/SKILL.md`
- Skills de dominio autocontenidas. Estándar `agentskills.io`.
- Cada una con frontmatter `--- name / description ---` (la `description` es lo
  que las herramientas leen para descubrir la skill).
- Regla de oro: `AGENTS.md` + `SKILL.md` son el único hogar de reglas/lecciones.

### 4. `.agents/agents/<name>.md`
- Roles de agente: quién hace qué (developer, reviewer, security…).
- Separar "rol" (persona) de "skill" (capacidad/dominio).

### 5. `.agents/README.md`
- "Project Brain": explica la estructura, la regla de oro y qué es público/privado.

### 6. `llms.txt` y `llms-full.txt`
- `llms.txt`: índice breve para indexadores/crawlers de IA (qué es, notas
  legales, enlaces a la documentación).
- `llms-full.txt`: contexto expandido en un solo fichero.
- **Ambos públicos y versionados.** Incluir una nota: "AI readability does NOT
  constitute a license grant".

### 7. Split público / privado
<!-- >>> startai:if-ai-private >>>
- `.gitignore`: ignorar `**/AGENTS.md`, `.agents/`, `CLAUDE.md`, `.claude/`,
  notas/planes personales, herramientas de dev y secretos.
- `.devinignore`: fichero gitignored con negaciones `!` que des-ignoran lo
  privado **solo para las tools del agente** (read/edit/grep). Git no lo lee.
- **Nunca** negar secretos (`*.key`, `*.pem`, `.env*`) ni artefactos
  (`target/`, `dist/`, `node_modules/`) en `.devinignore`.
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
- `ai_files_visibility="public"`: el contexto IA (`**/AGENTS.md`, `.agents/`,
  `CLAUDE.md`, `.claude/`) SE VERSIONA — compartido con el equipo.
- `.gitignore`: siguen privadas las notas/planes personales, herramientas de
  dev, secretos e ignore-files de agente.
- `.devinignore`: des-ignora lo privado restante **solo para las tools del
  agente**. **Nunca** negar secretos ni artefactos.
<!-- <<< startai:endif <<<

### 8. (Opcional) Bridge y orquestador
- `CLAUDE.md` con `@AGENTS.md` para Claude Code.
- Orquestador custom (`roles/`, `workflows/`, `memory/`, `state/`) si el equipo
  usa un dev-agent orquestador.

### 9. Adopción en un proyecto existente (capas)

Cuando el proyecto ya existe, aplicar el kit por capas, no de golpe:

- **Capas**: `agents` (AGENTS.md, .agents/, llms*.txt) → `hooks` → `audit` →
  `docs` → `distribution` → `release` (esta última requiere `audit`).
- **Preflight antes de aplicar**: detectar tokens `{{ x }}`/`{ALL-CAPS}` que
  romperían el check de coherencia, rutas privadas ya trackeadas, hooks de
  git preexistentes, generadores de docs en conflicto y paridad EN/ES.
- **Nunca sobrescribir**: conflictos → `<ruta>.startai-new`. El bloque de
  `.gitignore` se aplica **siempre** (el manifiesto `.startai-adopt.json`
  debe quedar ignorado); el de `.devinignore` solo con la capa `agents`.
- **Enforcement opt-in**: los hooks se entregan pero no se instalan; las
  entradas del perfil de auditoría sin fichero destino se comentan.
- **Vía manual**: renderizar antes de copiar (staging con `--emit-dir`) —
  nunca `cp` desde `templates/`, que lleva placeholders sin resolver.
- **Manifiesto `.startai-adopt.json`**: registra capas y hashes para que la
  re-adopción sea idempotente (upgrade solo de ficheros no editados).

### 10. `ai_files_visibility` y marcadores condicionales (kit)

- **`ai_files_visibility`** (clave de config, `"private"` por defecto):
  gobierna si el contexto IA (`**/AGENTS.md`, `.agents/`, `CLAUDE.md`,
  `.claude/`) es privado (gitignored) o público (versionado). Los secretos y
  lo privado del propietario NUNCA cambian de modo; solo esa clase es
  gobernada. Valor fuera de `{private, public}` = error fatal en generación,
  `adopt`, wizard y `check.py` (no depende de `--strict`).
- **Re-aplicación**: el cambio post-generación se hace re-corriendo `adopt`
  (el flag se persiste en el manifiesto; precedencia: `--config` >
  `config.json` del proyecto > manifiesto > `private`). Un flip
  public→private no des-publica: los ficheros ya trackeados requieren
  `git rm --cached` y el historial no se purga.
- **Marcadores condicionales** (solo en `templates/` del kit; nunca llegan
  al render): bloques de líneas centinela `if-ai-private` / `if-ai-public`
  cerrados por `endif`, con la sintaxis de comentario propia de cada fichero
  (`#` o `<!-- -->`), una línea por borde de bloque. Malformados, anidados,
  sin pareja o desconocidos = error fatal en `collect()`/`self_check`.
  Prohibidos en `.json` y en ficheros de `DOCS_COPY_PATHS` (sin sintaxis de
  comentario / copia verbatim). En prosa se citan por nombre, nunca con su
  prefijo literal — se auto-consumiría en `collect()`.

## Patrones obligatorios

```bash
# ✅ Crear una skill con frontmatter
mkdir -p .agents/skills/<name>
# SKILL.md empieza con: --- name: <name> / description: <...> ---

<!-- >>> startai:if-ai-private >>>
# ✅ Split privado: AGENTS.md y .agents/ gitignored
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
# ✅ Contexto IA versionado (ai_files_visibility="public")
<!-- <<< startai:endif <<<
# ✅ Split de acceso: .devinignore los des-ignora solo para tools
```

## Anti-patrones prohibidos

```bash
# ❌ Copiar reglas en varios ficheros (README + AGENTS.md + skill)
# ❌ Negar secretos en .devinignore (entrarían en contexto del agente)
# ❌ AGENTS.md anidado duplicando el índice completo de la raíz
# ❌ llms.txt con enlaces rotos o sin nota legal
# ❌ Rutas privadas en docs públicos: en documentación pública las skills se
#    citan por NOMBRE (`ai-native` skill), nunca por ruta; `.agents/`,
#    `scripts/dev/`, `docs/dev/` no aparecen en cabeceras de Referencias ni
#    como punteros — barrera mecánica: check 24_public_doc_refs de la
#    auditoría (los ficheros tutorial se allowlistan en el perfil).
```

## Cross-references
- Para el sitio estático y docs bilingües → ver `github-pages/SKILL.md`
- Para README/GIF/About → ver `distribution/SKILL.md`
