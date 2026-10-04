---
name: security
description: Anti-leak rules for a public repo — secrets never committed, public/private split with .devinignore contract, staged-blob scanning pre-commit hook, strict audit gate before push
---

# Security

## Cuándo usar esta skill
- Antes de hacer commit o push (el repo es **público**).
- Al manejar secretos, credenciales o ficheros de configuración reales.
- Al añadir una nueva ruta privada al `.gitignore` o tocar `.devinignore`.
- Al ejecutar o extender la auditoría (`scripts/dev/audit/`).

## Anti-filtración (regla base)

El repo es público. **Nunca** debe aparecer en ficheros versionados:

- Credenciales, contraseñas, tokens, API keys.
- Claves privadas (`*.key`, `*.pem`, `*.p12`, `*.pfx`).
- Ficheros de entorno o datos reales del propietario (`.env*`, `config.json`).
- Datos personales, rutas de home, topología o detalles de infraestructura
  privada del operador.

**Regla práctica:** si dudas de si algo es privado → no lo versiones. El coste
de un leak en un repo público es irreversible (el historial lo conserva).

## Split público / privado

El mecanismo completo (qué se versiona, qué se gitignora, cómo `.devinignore`
des-ignora lo privado solo para las tools del agente) vive en
`ai-native/SKILL.md`. Aquí solo las reglas de seguridad:

- **`.devinignore` NUNCA niega secretos ni artefactos** — solo des-ignora
  docs/tooling privados (`*.key`, `*.pem`, `.env*`, `feed/minisign.key`,
  `config.json`, `target/`, `dist/`, `*.log` quedan prohibidos como negación).
- Si añades una ruta privada nueva al `.gitignore`, añádela también a las
  listas canónicas del perfil de auditoría
  (`scripts/dev/audit/profiles/project.conf`: `REQUIRED_GITIGNORE`,
  `PRIVATE_GLOBS`) y a la lista duplicada del hook `scripts/git/pre-commit`
  — están duplicadas a propósito (un clon limpio no tiene el perfil privado).
- **`ai_files_visibility`**: la clase "contexto IA" (`**/AGENTS.md`,
  `.agents/`, `CLAUDE.md`, `.claude/`) puede ser privada (default) o pública
  según ese flag de generación; los secretos y lo privado del propietario
  son siempre privados. En modo `public` las entradas IA desaparecen de
  `.gitignore`, del hook y del perfil — el resto del enforcement no cambia.
  La convención de marcadores condicionales de las plantillas del kit vive
  en `ai-native/SKILL.md` §10.

## Barreras mecánicas (no depender de la memoria)

| Barrera | Cuándo actúa | Qué bloquea |
|---------|--------------|-------------|
| `scripts/git/pre-commit` | cada `git commit` | Secretos en **blobs staged** (`git show ":$file"`), rutas privadas staged, `.gitignore` staged sin los patrones privados, `.devinignore` que niega secretos, rutas staged que contengan un término de `forbidden-terms.conf` |
| `scripts/git/commit-msg` | cada `git commit` | Trailers de atribución IA (`Co-Authored-By:`, `Generated with`…) y términos privados del conf — el autor/firmante es solo el humano |
| `scripts/git/pre-push` | cada `git push` | Tests + auditoría `--strict` + nombres de rama/tag que contengan un término privado del conf |
| `run_all.sh --strict` | manual / hook / release | Checks `01` (secretos en la superficie publicada), `23` (rutas privadas, integridad de `.gitignore`/`.devinignore`, y 23.5: términos privados del conf en ficheros trackeados) y `24` (referencias a rutas privadas en docs públicos — skills citadas por nombre, no por ruta; cubre también CHANGELOG/llms vía `PRIVATE_REF_SCAN_FILES`, con `PRIVATE_REF_IGNORE_RE` para menciones legítimas), entre otros |

### Términos que son ellos mismos privados

Marcas, metodología interna o topología cuyo propio texto no puede aparecer
en ficheros versionados (ni siquiera en la lista de un hook público). Se
escriben en `scripts/dev/forbidden-terms.conf` (gitignored, un ERE por
línea) y los hooks + el check 23.5 los cargan en runtime; override de tests
`STARTAI_PRIVATE_TERMS_FILE`. Si el conf falta, el chequeo se desactiva —
no rompe clones públicos, pero revisa que exista tras instalar el tooling.

Antes de cada push:

```bash
bash scripts/dev/audit/run_all.sh --profile project --strict
```

Exit codes: `0` OK · `1` errores bloqueantes · `2` solo warnings (en
`--strict` también bloquea). Cada check imprime una sentinela
`AUDIT_RESULT check=<nombre> errors=N warnings=N` que `run_all.sh` usa como
fuente de verdad — al extender la auditoría, nunca llamar a
`log_error`/`log_warning` en la rama derecha de un `|` (el subshell pierde
los contadores); capturar en variable y recorrer con `<<<` herestring.

## Secretos en el día a día

- Guardar claves **fuera del repo** (`~/.minisign/`, etc.) con permisos
  `0600` — la skill `signing` detalla la gestión de claves de firma.
- `git commit --no-verify` es un escape puntual y documentado, jamás el
  procedimiento habitual.
- Si el pre-commit bloquea algo legítimo, la vía correcta es añadir la ruta a
  la lista de exclusión del propio hook explicando el motivo — nunca
  desactivar el escaneo.
- Nunca escribir passphrases ni credenciales a fichero "temporalmente".

## Anti-patrones prohibidos

```bash
# ❌ git add -A sin revisar git status (puede arrastrar rutas privadas)
# ❌ Negar *.key / .env* / config.json en .devinignore
# ❌ Commitear feed/minisign.key (la .pub sí es pública)
# ❌ Borrar un patrón privado del .gitignore "porque molesta"
# ❌ Push sin pasar run_all.sh --strict
# ❌ Trailers de atribución IA en el mensaje de commit
```

## Cross-references
- Para el split público/privado y `.devinignore` → ver `ai-native/SKILL.md`
- Para la firma de releases y gestión de claves → ver `signing/SKILL.md`
- Para el feed firmado → ver `updates/SKILL.md`
- Para el pipeline de release (la auditoría es su paso 1) → ver `release/SKILL.md`
