# Kit de plantillas (scaffold)

Este directorio contiene las **plantillas del proyecto**: identidad (`README`,
`AGENTS.md`, `llms.txt`…), `.agents/` (contexto IA genérico), `scripts/`
(check, github, hooks) y las páginas de identidad de `docs/`. Los ficheros que
además se copian **desde la raíz** del repo `startai` son: `LICENSE`,
`SECURITY.md`, `CONTRIBUTING.md`, `THIRD_PARTY_LICENSES.md` y las
guías/assets/layout de `docs/`.

## Cómo generar un proyecto nuevo

Usa el script interactivo (Python 3, sin dependencias):

```bash
python3 scripts/startai.py mi-nuevo-proyecto                        # interactivo
python3 scripts/startai.py mi-nuevo-proyecto --config config.json   # no-interactivo
python3 scripts/startai.py mi-nuevo-proyecto --no-review            # sin revisión
```

El script:

1. Pregunta por cada variable de `config.example.json` (Enter = valor por defecto).
   Con `--config` lee el JSON y no pregunta nada.
2. Renderiza esta carpeta `templates/` + los ficheros genéricos de la raíz,
   sustituyendo las variables `{{clave}}`.
3. Recorre cada fichero generado mostrando su contenido y ofreciendo:
   `[k] mantener · [e] editar · [r] sustituir por un fichero existente (ruta) · [s] eliminar · [a] mantener todos los restantes`.

## Variables de configuración

Las variables se definen en `config.example.json` (raíz). En los templates se
referencian como `{{clave}}`. Variables principales:

| Clave | Uso |
|-------|-----|
| `{{product_name}}` | Nombre del software |
| `{{product_slug}}` | Nombre del binario/comando |
| `{{owner}}` | Titular del copyright (nombre legal) |
| `{{email}}` | Contacto seguridad/licencia |
| `{{year}}` | Año(s) de publicación |
| `{{github_user}}` | Usuario de GitHub (URLs) |
| `{{repo}}` | Nombre del repositorio (URLs) |
| `{{version}}` | Versión inicial |
| `{{platform}}`, `{{language}}`, `{{architecture}}` | Plataforma/stack/arquitectura |
| `{{tagline}}`, `{{description}}`, `{{purpose}}` | Frases de presentación |
| `{{install_command}}`, `{{command_tree}}`, `{{dir_structure}}` | Instalación/comandos/estructura |
| `{{feature_1..3}}` | Características del README |

## Contenido de esta carpeta

| Plantilla | Destino en el proyecto |
|-----------|------------------------|
| `README.en.md` | `README.md` |
| `README.es.md` | `README.es.md` |
| `AGENTS.md` | `AGENTS.md` |
| `llms.txt` / `llms-full.txt` | idem (raíz) |
| `CHANGELOG.md` | `CHANGELOG.md` |
| `gitignore` / `.devinignore` | `.gitignore` / `.devinignore` — split público/privado del proyecto generado (`gitignore` se renombra a `.gitignore` al generar; el nombre sin punto evita que actúe como gitignore anidado dentro de `templates/` en este repo) |
| `.agents/` (`README.md`, `agents/`, `skills/`) | contexto IA genérico (gitignored en el proyecto generado) |
| `scripts/check.py` | chequeos de coherencia del proyecto generado (config.json, tokens, bilingüe) |
| `scripts/github.py` | publicación a GitHub + Pages (desde consola) |
| `scripts/git/` (`pre-commit`, `pre-push`, `commit-msg`, `install-hooks.sh`) | hooks de git |
| `scripts/dev/` (`audit/`, `session_start.sh`, `context-gen.py`, `sync_version.sh`, `release.sh`) | tooling de desarrollo: auditoría, contexto de sesión, sync de versión y pipeline de release (en el proyecto generado `scripts/dev/` es privado/gitignored) |
| `docs/_config.yml`, `docs/index.md`, `docs/en/index.md`, `docs/es/index.md` | páginas de identidad del sitio |

> `README.md` de esta carpeta (este fichero) **no** forma parte del scaffold; es
> la documentación del kit.
