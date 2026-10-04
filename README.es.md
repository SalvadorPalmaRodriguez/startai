# startai — Kit de proyectos AI-native y listos para distribuir

**[English](README.md)** · **Español**

> Un repositorio de documentación con **procesos y plantillas reutilizables y agnósticos a cualquier proyecto** que responden a dos preguntas:
>
> 1. **¿Cómo convierto un proyecto normal en un proyecto AI-native?** — `AGENTS.md`, `.agents/` (agents + skills), `llms.txt` / `llms-full.txt` y la separación público/privado para que los agentes IA trabajen sin filtrar secretos.
> 2. **¿Cómo dejo un proyecto listo para su distribución en un repositorio?** — `README` bilingüe + plantillas de sitio estático, artefactos de distribución, visibilidad/promoción, licencia y un modelo de doble firma de releases.

Todo aquí está **guiado por configuración**: los valores específicos del proyecto viven en un único fichero (`config.example.json`) y el generador interactivo `scripts/startai.py` crea un proyecto nuevo a partir de ellos — sin buscar placeholders a mano.

---

## Qué contiene

| Área | Dónde | Propósito |
|------|-------|-----------|
| Desarrollo AI-native | `templates/AGENTS.md`, `templates/.agents/`, `templates/llms.txt`, `templates/llms-full.txt` | Reglas, skills y roles de agente que se generan en proyectos nuevos (privados por defecto — gobernado por `ai_files_visibility`). |
| Distribución y promoción | `README.md`, `docs/`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | README bilingüe, plantillas de sitio estático bilingüe, ficheros legales/comunidad. |
| Licencias | `LICENSE`, `THIRD_PARTY_LICENSES.md` | Licencia propietaria de código visible (nombre como placeholder) + avisos de terceros. |
| Firma de releases | `templates/.agents/skills/signing/`, `docs/*/signing.md` | Modelo de doble firma (minisign Ed25519 + ML-DSA-65 post-cuántica) y verificación offline. |
| Config & scaffolding | `config.example.json`, `scripts/startai.py` | Única fuente de verdad para las variables + generador interactivo. |
| Plantillas listas para copiar | `templates/` | Plantillas de identidad renderizadas por el generador. |

## Las dos guías principales

- **[Convertir un proyecto en AI-native](docs/es/ai-native.md)** ([EN](docs/en/ai-native.md)) — el proceso exacto, paso a paso.
- **[Preparar un proyecto para distribución](docs/es/distribution.md)** ([EN](docs/en/distribution.md)) — plantillas de README y sitio, artefactos de distribución, visibilidad y promoción.

## Generar un proyecto nuevo

```bash
python3 scripts/startai.py mi-proyecto                          # interactivo
python3 scripts/startai.py mi-proyecto --config config.json     # no-interactivo
python3 scripts/startai.py mi-proyecto --config config.json --dry-run                # previsualizar
python3 scripts/startai.py mi-proyecto --config config.json --dry-run --dry-run-output preview.txt  # previsualizar + guardar
python3 scripts/startai.py mi-proyecto --config config.json --strict                  # abortar si hay valores vacíos
python3 scripts/startai.py mi-proyecto --no-review              # sin revisión
python3 scripts/startai.py --check                             # validar config + templates
```

`python3 scripts/startai.py --help` lista todas las opciones; `scripts/github.py --help`
lista los subcomandos de publicación.

El script (Python 3, sin dependencias) te pregunta por cada variable, renderiza
las plantillas en un directorio nuevo y te guía por cada fichero de texto
generado (`config.json` y los binarios quedan fuera de ese pase). En la
revisión, cada fichero puede `[k]` mantenerse, `[e]` editarse en tu editor,
`[r]` sustituirse por un fichero existente (indicando su ruta), `[s]`
eliminarse o `[a]` mantenerse junto a todos los restantes. Con `--config` lee
un JSON y renderiza sin preguntar nada.

El argumento posicional es el **directorio destino**: cualquier ruta relativa o
absoluta, no solo un nombre — `python3 scripts/startai.py ../mi-proyecto` crea
el proyecto al lado de este kit en lugar de dentro — la disposición
recomendada. Si se omite, el nombre del directorio usa el valor de
`product_slug` de la configuración. El directorio debe estar vacío o no
existir; si no, el script aborta. Tras renderizar, la configuración resuelta se
guarda en `<destino>/config.json` para poder regenerar el proyecto más tarde.

La configuración siempre se valida: los valores explícitamente vacíos provocan
un `WARNING` (con `--strict` abortan en su lugar), mientras que las claves
ausentes de un `--config` heredan los defaults de `config.example.json` en
silencio — rellénalas todas para un render totalmente controlado. `--dry-run`
muestra la configuración resuelta y el contenido renderizado completo de cada
fichero sin escribir nada en disco; añade `--dry-run-output FICHERO` para
guardar la previsualización (sin efecto sin `--dry-run`).

Los proyectos generados también incluyen el tooling reutilizado, todo
versionado/público: `scripts/check.py` (chequeos de coherencia),
`scripts/github.py` (publicación) y `scripts/git/` (hooks git — instalar con
`bash scripts/git/install-hooks.sh`). También incluyen `scripts/dev/`
(framework de auditoría, `session_start.sh`, `context-gen.py`,
`sync_version.sh`, `release.sh`), que el `.gitignore` generado mantiene
privado — el tooling de desarrollo viaja con el proyecto pero no se publica.

## Adoptar el kit en un proyecto existente

`startai.py adopt` lleva capas seleccionadas del kit a un proyecto que ya
existe (el modo scaffold rechaza directorios no vacíos). Dos reglas de
seguridad están integradas: **adopt nunca escribe sin `--apply`**, y **nunca
sobrescribe** un fichero en conflicto — escribe `<ruta>.startai-new` en su
lugar — ni instala hooks de git (el enforcement siempre es opt-in). El
destino por defecto es el directorio actual — pásalo explícitamente para ir
seguro.

```bash
python3 scripts/startai.py adopt /ruta/al/proyecto --report                  # solo preflight (por defecto)
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --layers agents   # escribir una capa
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --all-layers      # escribir todas las capas
python3 scripts/startai.py adopt --list-layers                               # tabla de capas
python3 scripts/startai.py adopt /ruta/al/proyecto --manual                  # checklist manual
python3 scripts/startai.py adopt /ruta/al/proyecto --emit-dir /tmp/staging   # renderizar en DIR, target intacto
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --config cfg.json # escritura no-interactiva
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --infer-only      # valores inferidos, sin wizard
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --force           # continuar a pesar de BLOCKERs
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --overwrite       # reemplazar conflictos
python3 scripts/startai.py adopt /ruta/al/proyecto --strict                  # los warnings también bloquean
```

Sin `--config` ni `--infer-only`, `--apply` y `--emit-dir` lanzan el wizard
interactivo (las mismas preguntas que al generar); en modo `--report` se usan
los valores inferidos en silencio.

### Capas

| Capa | Contenido | Riesgo |
|------|-----------|--------|
| `agents` (por defecto) | `AGENTS.md`, `.agents/` (skills, roles, orquestador), `llms.txt`, `llms-full.txt`, bloque de `.devinignore` | bajo — solo aditivo |
| `hooks` | hooks `scripts/git/` + `scripts/check.py` | alto — bloquea commits si hay tokens o rutas privadas en colisión (el preflight lo detecta) |
| `audit` | framework de auditoría `scripts/dev/` | medio — el perfil strict avisa si falta CHANGELOG/README.es/llms-full |
| `docs` | sitio Jekyll bilingüe EN/ES en `docs/` | alto — colisiona con mkdocs/Docusaurus/Sphinx |
| `distribution` | `README*.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `THIRD_PARTY_LICENSES.md`, `.github/` | alto — probable conflicto con ficheros existentes |
| `release` | `feed/`, `scripts/github.py` (requiere `audit`) | medio |

Flujo recomendado: `--report` → corregir o deseleccionar según los BLOCKERs →
`--apply --layers agents` → añadir capas incrementalmente. Un manifiesto
`.startai-adopt.json` guarda hashes y capas adoptadas, así que re-ejecutar
adopt es idempotente y solo actualiza ficheros que no has editado desde
la adopción.

El bloque gestionado de `.gitignore` se aplica en **todo** `--apply`,
independientemente de las capas elegidas (el propio manifiesto debe quedar
ignorado), mientras que `.devinignore` solo la toca la capa `agents`.

`--emit-dir DIR` renderiza las capas seleccionadas en `DIR` **sin tocar el
destino** — sirve para diffear el resultado contra tu repo con tus propias
herramientas, o como primer paso de la adopción manual. No viola la regla
«no escribe sin `--apply`»: solo escribe en el directorio que nombras
explícitamente, nunca en el destino. `--emit-dir` anula a `--apply`: si
pasas ambos, solo ocurre el emit.

Códigos de salida: `0` limpio (incluido un `--apply` forzado que superó
BLOCKERs) · `1` hay BLOCKERs — report/emit/apply abortado — o WARNINGs con
`--strict` (aunque la escritura se haya completado) · `2` error de uso (capa
desconocida o `--layers` vacío, destino que no es directorio, `--config`
ilegible, `ai_files_visibility` inválido).

### Chequeos del preflight (y por qué existen)

Cada chequeo corre **solo cuando la capa que protege está seleccionada** —
p.ej. el escaneo de tokens con `hooks`, las rutas privadas trackeadas con
`hooks`/`audit`:

- **Placeholders `{{token}}`/`{ALL_CAPS}` colisionantes** (BLOCKER): tokens
  `{{nombre}}` sin espacios (estilo Handlebars) o placeholders legados
  `{ALL_CAPS}`/`{YYYY-MM-DD}` — los mismos patrones que el `check.py` generado
  rechaza en cada commit. La sintaxis con espacios o puntos (Jekyll
  `{{ page.title }}`, Go `{{.Field}}`, Liquid `{% … %}`) **no** colisiona.
- **Rutas privadas ya trackeadas por git** (BLOCKER): el paso 3 del
  pre-commit y el check 23 de auditoría fallarían (`AGENTS.md`, `.agents/`,
  `*.key`, …).
- **Scripts previos en `.git/hooks/` o `core.hooksPath`** (BLOCKER/WARN):
  `install-hooks.sh` los sobrescribiría o sería ignorado silenciosamente.
- **Generador de docs ya presente** (BLOCKER): MkDocs, Docusaurus,
  Sphinx/Jekyll, o un framework de docs en `package.json`.
- **Paridad bilingüe, prerrequisitos de auditoría, árbol sucio** (WARN): lo
  que el perfil strict reclamará después.
- **Dependencias de capa** (BLOCKER): p.ej. `release` sin `audit`.
- **Flips de `ai_files_visibility`** (WARN/BLOCKER): el modo resuelto difiere
  del del manifiesto y las capas de enforcement (`agents`,`hooks`,`audit`) no
  están todas seleccionadas; con `private` y ficheros IA ya trackeados añade
  remediación `git rm --cached`.

### Adopción manual

`--manual` imprime un checklist copiable derivado del mismo manifiesto de
capas. Es un flujo de dos fases — nunca `cp` desde `templates/` directamente
(esos ficheros llevan `{{tokens}}` sin resolver que `check.py` rechazaría):
primero renderiza con `--emit-dir`, luego copia los ficheros renderizados y
añade los bloques marcados de `.gitignore`/`.devinignore`. Es una vía
soportada, pero sin el manifiesto las re-ejecuciones no distinguen ficheros
del kit de tus ediciones — ejecuta `--report` antes en cualquier caso. Una
consecuencia: el paso de añadido no es idempotente como sí lo es `--apply`,
así que en una adopción manual repetida borra el bloque
`# >>> startai >>>` existente antes de añadir el nuevo, o acabarás con dos
bloques.

## Estructura del proyecto generado

```
project/
├── AGENTS.md              # punto de entrada canónico para cualquier agente IA (reglas + índice de skills)
├── README.md / README.es.md
├── llms.txt / llms-full.txt        # contexto público legible por IA
├── config.json            # config de generación resuelta (privada — estado del propietario)
├── LICENSE                # propietaria de código visible (bilingüe, nombre placeholder)
├── THIRD_PARTY_LICENSES.md
├── SECURITY.md · CONTRIBUTING.md · CHANGELOG.md
├── .gitignore · .devinignore       # separación público/privado
├── .github/ISSUE_TEMPLATE/  # formularios de issues públicos (bug, feature, contact links)
├── .agents/               # privado por defecto — ver ai_files_visibility
│   ├── agents/            # roles de agente (quién hace qué)
│   ├── skills/<name>/SKILL.md      # skills de dominio autocontenidas (10 incluidas)
│   └── orchestrator/      # contrato opcional de orquestador de agentes (roles, workflows, memoria)
├── feed/                  # feed de actualizaciones firmado (advisories.json + README)
├── scripts/
│   ├── check.py           # chequeos de coherencia del proyecto
│   ├── github.py          # publicación en GitHub + Pages
│   ├── git/               # hooks de git (opt-in vía install-hooks.sh)
│   └── dev/               # tooling de dev privado: auditoría, session_start, release
└── docs/                  # sitio estático GitHub Pages (Jekyll, bilingüe EN/ES)
    ├── index.md · README.md
    ├── _config.yml · _layouts/default.html · assets/ (css, logo, social preview)
    ├── en/                # guías en inglés
    └── es/                # guías en español
```

El split del `.gitignore` lo gobierna `ai_files_visibility` en la config:
`"private"` (por defecto) mantiene los ficheros de contexto IA (`AGENTS.md`,
`.agents/`, `CLAUDE.md`, `.claude/`) fuera de git; `"public"` los versiona
para el equipo. Los secretos y lo privado del propietario siguen bloqueados
en ambos modos.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Una suite de tests en cinco capas — **unitarios** (sustitución de tokens,
carga y validación de config, acciones de revisión, construcción de comandos
de GitHub, centineles de visibilidad), **adopción** (`adopt` plan/apply/emit,
manifiesto, findings del preflight, flips de visibilidad), **hooks**
(escaneos de blobs staged, rutas privadas), **integración** (árbol generado,
coherencia plantillas/config, sin tokens sin resolver, split de .gitignore,
ejecutabilidad de scripts, `check.py`) y **end-to-end** (modos de CLI:
`--help`, `--config`, `--dry-run`, `--dry-run-output`, `--strict`, `--check`,
wizard, aviso de valor vacío, protección de directorio no vacío).

## Publicar en GitHub

Todo desde consola, sin navegador. Requiere la CLI de GitHub (`gh`):

1. Instala los hooks de git (validación + anti-secretos + sin commits de atribución IA):
   ```bash
   bash scripts/git/install-hooks.sh
   ```

2. Crea el repo, configura el About (homepage + topics) y el remoto `origin`:
   ```bash
   python3 scripts/github.py create --owner <usuario> --repo <repo> --description "..." --topic cli
   ```

3. Haz commit y push:
   ```bash
   git add -A && git commit -m "Initial commit" && git push -u origin main
   ```

4. Activa GitHub Pages (servido desde `docs/`) y dispara el build:
   ```bash
   python3 scripts/github.py pages --owner <usuario> --repo <repo>
   python3 scripts/github.py status --owner <usuario> --repo <repo>
   ```

Tu web quedará en `https://<usuario>.github.io/<repo>/`.

## Licencia

`startai` en sí se licencia bajo **propietaria de código visible**: privada, con
código visible y solo uso personal — ver [LICENSE](LICENSE). El generador
produce esa misma licencia para los proyectos nuevos desde `templates/LICENSE`,
rellenando sus variables `{{product_name}}`, `{{owner}}`, `{{email}}` y
`{{year}}` desde `config.example.json`. Ver la [guía de licencias](docs/es/license.md).

---

📄 **[llms.txt](llms.txt)** para indexadores de IA — la legibilidad por IA **no** constituye concesión de licencia; ver [LICENSE](LICENSE).
