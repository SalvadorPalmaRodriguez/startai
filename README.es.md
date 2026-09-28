# startai — Kit de proyectos AI-native y listos para distribuir

**[English](README.md)** · **Español**

> Un repositorio de documentación con **procesos y plantillas reutilizables y agnósticos a cualquier proyecto** que responden a dos preguntas:
>
> 1. **¿Cómo convierto un proyecto normal en un proyecto AI-native?** — `AGENTS.md`, `.agents/` (agents + skills), `llms.txt` / `llms-full.txt` y la separación público/privado para que los agentes IA trabajen sin filtrar secretos.
> 2. **¿Cómo dejo un proyecto listo para su distribución en un repositorio?** — `README` bilingüe, GIF de demostración, sitio estático en GitHub Pages, apartado "About" de GitHub, visibilidad/promoción, licencia y firma de releases.

Todo aquí está **guiado por configuración**: los valores específicos del proyecto viven en un único fichero (`config.example.json`) y el generador interactivo `scripts/startai.py` crea un proyecto nuevo a partir de ellos — sin buscar placeholders a mano.

---

## Qué contiene

| Área | Dónde | Propósito |
|------|-------|-----------|
| Desarrollo AI-native | `templates/AGENTS.md`, `templates/.agents/`, `templates/llms.txt`, `templates/llms-full.txt` | Reglas, skills y roles de agente que se generan en proyectos nuevos (privados allí, vía `templates/.gitignore`). |
| Distribución y promoción | `README.md`, `docs/`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | README bilingüe, GIF de demo, sitio estático GitHub Pages, About/topics/badges. |
| Licencias | `LICENSE`, `THIRD_PARTY_LICENSES.md` | Licencia propietaria de código visible (nombre como placeholder) + avisos de terceros. |
| Firma de releases | `templates/.agents/skills/signing/`, `docs/*/signing.md` | Ceremonia de firma minisign (Ed25519) + ML-DSA-65 post-cuántica. |
| Config & scaffolding | `config.example.json`, `scripts/startai.py` | Única fuente de verdad para las variables + generador interactivo. |
| Plantillas listas para copiar | `templates/` | Plantillas de identidad renderizadas por el generador. |

## Las dos guías principales

- **[Convertir un proyecto en AI-native](docs/es/ai-native.md)** ([EN](docs/en/ai-native.md)) — el proceso exacto, paso a paso.
- **[Preparar un proyecto para distribución](docs/es/distribution.md)** ([EN](docs/en/distribution.md)) — README, GIF, página GitHub.io, apartado About, visibilidad y promoción.

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
las plantillas en un directorio nuevo y recorre cada fichero generado. En la
revisión, cada fichero puede `[k]` mantenerse, `[e]` editarse con tu editor,
`[r]` sustituirse por un fichero existente (indicando su ruta) o `[s]`
eliminarse. Con `--config` lee un JSON y renderiza sin preguntar nada.

El argumento posicional es el **directorio destino**: cualquier ruta relativa o
absoluta, no solo un nombre — `python3 scripts/startai.py ../mi-proyecto` crea
el proyecto al lado de este kit en lugar de dentro (recomendado). Si se omite,
usa `product_slug` de la configuración. El directorio debe estar vacío o no
existir; si no, el script aborta. Tras renderizar, la configuración resuelta se
guarda en `<destino>/config.json` para poder regenerar el proyecto más tarde.

La configuración siempre se valida: los valores vacíos o faltantes imprimen un
`WARNING` (con `--strict` abortan en su lugar). `--dry-run` muestra la
configuración resuelta y el contenido renderizado completo de cada fichero sin
escribir nada en disco; añade `--dry-run-output FICHERO` para guardar la
previsualización.

Los proyectos generados también incluyen el tooling reutilizado, todo
versionado/público: `scripts/check.py` (chequeos de coherencia),
`scripts/github.py` (publicación) y `scripts/git/` (hooks git — instalar con
`bash scripts/git/install-hooks.sh`). También incluyen `scripts/dev/`
(framework de auditoría, `session_start.sh`, `context-gen.py`,
`sync_version.sh`, `release.sh`), que el `.gitignore` generado mantiene
privado — el tooling de desarrollo viaja con el proyecto pero no se publica.

## Adoptar el kit en un proyecto existente

`startai.py adopt` lleva capas seleccionadas del kit a un proyecto que ya
existe (el scaffold `new` rechaza directorios no vacíos). Dos reglas de
seguridad están integradas: **adopt nunca escribe sin `--apply`**, y **nunca
sobrescribe** un fichero en conflicto — escribe `<ruta>.startai-new` en su
lugar — ni instala hooks de git (el enforcement siempre es opt-in).

```bash
python3 scripts/startai.py adopt /ruta/al/proyecto --report                  # solo preflight (por defecto)
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --layers agents   # escribir una capa
python3 scripts/startai.py adopt --list-layers                               # tabla de capas
python3 scripts/startai.py adopt /ruta/al/proyecto --manual                  # checklist manual
python3 scripts/startai.py adopt /ruta/al/proyecto --emit-dir /tmp/staging   # renderizar en DIR, target intacto
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --force           # continuar a pesar de BLOCKERs
python3 scripts/startai.py adopt /ruta/al/proyecto --apply --overwrite       # reemplazar conflictos
python3 scripts/startai.py adopt /ruta/al/proyecto --strict                  # los warnings también bloquean
```

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
entonces.

El bloque gestionado de `.gitignore` se aplica en **todo** `--apply`,
independientemente de las capas elegidas (el propio manifiesto debe quedar
ignorado), mientras que `.devinignore` solo la toca la capa `agents`.

`--emit-dir DIR` renderiza las capas seleccionadas en `DIR` **sin tocar el
destino** — sirve para diffear el resultado contra tu repo con tus propias
herramientas, o como primer paso de la adopción manual. No viola la regla
«no escribe sin `--apply`»: solo escribe en el directorio que nombras
explícitamente, nunca en el destino.

Códigos de salida: `0` limpio · `1` hay BLOCKERs, o WARNINGs con `--strict`
(aunque la escritura se haya completado) · `2` error de uso (capa
desconocida, destino inexistente).

### Chequeos del preflight (y por qué existen)

- **Placeholders `{{token}}`/`{ALLCAPS}` colisionantes** (BLOCKER):
  `check.py` fallaría en cada commit con sintaxis Jekyll/Handlebars/Go-template.
- **Rutas privadas ya trackeadas por git** (BLOCKER): el paso 3 del
  pre-commit y el check 23 de auditoría fallarían (`AGENTS.md`, `.agents/`,
  `*.key`, …).
- **Scripts previos en `.git/hooks/` o `core.hooksPath`** (BLOCKER/WARN):
  `install-hooks.sh` los sobrescribiría o sería ignorado silenciosamente.
- **Generador de docs ya presente** (BLOCKER): mkdocs, Docusaurus,
  Sphinx/Jekyll, o un framework de docs en `package.json`.
- **Paridad bilingüe, prerrequisitos de auditoría, árbol sucio** (WARN): lo
  que el perfil strict reclamará después.
- **Dependencias de capa** (BLOCKER): p.ej. `release` sin `audit`.

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
`# >>> startai >>>` existente antes de añadir el nuevo, o acabarás con dos.

## Estructura de referencia

```
project/
├── AGENTS.md              # punto de entrada canónico para cualquier agente IA (reglas + índice de skills)
├── README.md / README.es.md
├── llms.txt / llms-full.txt        # contexto público legible por IA
├── LICENSE                # propietaria de código visible (bilingüe, nombre placeholder)
├── THIRD_PARTY_LICENSES.md
├── SECURITY.md · CONTRIBUTING.md · CHANGELOG.md
├── .gitignore · .devinignore       # separación público/privado
├── .github/ISSUE_TEMPLATE/  # formularios de issues públicos (bug, feature, contact links)
├── .agents/
│   ├── agents/            # roles de agente (quién hace qué)
│   ├── skills/<name>/SKILL.md      # skills de dominio autocontenidas
│   └── orchestrator/      # contrato opcional de orquestador de agentes (roles, workflows, memoria)
└── docs/                  # sitio estático GitHub Pages (Jekyll, bilingüe EN/ES)
    ├── _config.yml
    ├── _layouts/default.html
    ├── assets/            # css, logo, social preview
    ├── en/                # guías en inglés
    └── es/                # guías en español
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Una suite de tests en tres capas — **unitarios** (sustitución de tokens, carga y validación
de config, acciones de revisión, construcción de comandos de GitHub),
**integración** (árbol generado, coherencia plantillas/config, sin tokens sin
resolver, split de .gitignore, ejecutabilidad de scripts, `check.py`) y
**end-to-end** (modos de CLI: `--help`, `--config`, `--dry-run`,
`--dry-run-output`, `--strict`, `--check`, wizard, aviso de valor vacío,
protección de directorio no vacío).

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
