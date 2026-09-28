---
name: release
description: Release pipeline — semver bump decision, strict audit gate, version sync from CHANGELOG, signed update feed, signed git tag, packaged tarball with sha256 and minisign, GitHub release via scripts/dev/release.sh
---

# Release

## Cuándo usar esta skill
- Preparar o publicar un release (versionado, feed, tag, artefactos, GitHub).
- Decidir el bump semver de la próxima versión.
- Diagnosticar por qué `release.sh` aborta.

## Fuente única de versión

- La versión canónica del producto es el **primer `## [x.y.z]` de
  `CHANGELOG.md`** (`[Unreleased]` se ignora). NUNCA se edita a mano en otros
  ficheros: `scripts/dev/sync_version.sh` la propaga a los `VERSION_TARGETS`
  del perfil de auditoría (`scripts/dev/audit/profiles/*.conf`).
- `sync_version.sh --check` verifica coherencia; `--bump X.Y.Z` convierte la
  sección `[Unreleased]` en la entrada fechada y propaga; `--release-feed`
  actualiza `latest`/`published_at` de `feed/advisories.json` y lo re-firma
  (ver `updates/SKILL.md`).
- Las cabeceras `Versión:`/`Version:` de los docs son de DOCUMENTO — el
  release no las toca (ver `docs-update/SKILL.md`).

## Pipeline (`scripts/dev/release.sh`)

```bash
bash scripts/dev/release.sh                 # releasea la versión del CHANGELOG
bash scripts/dev/release.sh --bump X.Y.Z    # bump primero, luego release
bash scripts/dev/release.sh --dry-run       # imprime el plan, no muta nada
bash scripts/dev/release.sh --yes           # salta la confirmación de publicar
```

El script ejecuta, en orden:

0. **Precondiciones** — repo git en `main`/`master`, worktree limpio, `gh`
   autenticado, `python3`, `sha256sum`. `minisign` ausente → warning (la
   release sale **sin firmar**, no es bloqueante). Tag `vX.Y.Z` ya existente →
   aborta.
1. **Auditoría strict** — `run_all.sh --profile <perfil> --strict` (el primer
   `.conf` de `scripts/dev/audit/profiles/`). Fallo → aborta.
2. **Versión** — `sync_version.sh --bump X.Y.Z` si se pidió bump, si no
   `--check` (drift → aborta).
3. **Feed** — `sync_version.sh --release-feed` (re-firma si existe
   `feed/minisign.key`).
4. **Build opcional** — si el proyecto compila artefactos, engancharlo con
   `BUILD_CMD="make release" bash scripts/dev/release.sh`. En un proyecto de
   solo docs/scripts se omite.
5. **Commit + tag** — `git commit -S` (fallback: sin firmar + warning) y
   `git tag -s vX.Y.Z` (fallback: `-a` + warning).
6. **Empaquetado** — `git archive` → `dist/<repo>-vX.Y.Z.tar.gz` + `.sha256`
   + `.minisig` (clave: `$RELEASE_MINISIGN_KEY` → `feed/minisign.key` →
   `minisign.key` en raíz).
7. **Publicación** — confirmación interactiva (salvo `--yes`), push de rama +
   tag, `gh release create` con las notas extraídas de la sección `## [X.Y.Z]`
   del CHANGELOG.
8. **Resumen** — tag, assets y URL del release.

La identidad del repo (`gh release --repo`, nombre del tarball) se deriva de
`config.json` (`github_user`/`repo`) → `git remote origin` → nombre del
directorio.

## Puntos de decisión humana

- **Qué bump**: el script exige `X.Y.Z` explícito o la versión ya presente en
  el CHANGELOG — no auto-detecta. Semver: `fix:`/correcciones → patch,
  features retrocompatibles → minor, rupturas → major.
- **Contenido del CHANGELOG**: la entrada `## [X.Y.Z]` debe existir y tener
  cuerpo ANTES de lanzar (es lo que se publica como notas; si está vacía el
  paso 7 aborta). Prepararla es trabajo de `docs-update`, no del script.
- **Ceremonia PQC**: el pipeline firma con minisign; la firma ML-DSA-65 de
  artefactos es una ceremonia manual encima (ver `signing/SKILL.md`).
- **`--dry-run` primero** cuando haya dudas: imprime el plan y el estado de
  cada precondición sin mutar nada.

## Errores típicos

| Síntoma | Causa | Fix |
|---------|-------|-----|
| `CHANGELOG.md has no '## [x.y.z]'` | Falta la entrada | Escribirla (o `--bump X.Y.Z`) |
| `Dirty worktree` / `Not on the main branch` | Estado git incorrecto | Commit/stash y `git checkout main` |
| `Tag vX.Y.Z already exists` | Versión ya releaseada | Bump a la siguiente |
| `Audit failed` | El gate strict encontró errores | `run_all.sh --profile <perfil> --strict` y corregir |
| `No release notes` | Sección `## [X.Y.Z]` vacía | Rellenar el cuerpo del CHANGELOG |
| `gh CLI not authenticated` | Sin `gh auth login` | Autenticar `gh` |
| `artifact unsigned` (warning) | Sin `minisign` ni clave | Instalar minisign + clave (ver `signing`) |

## Anti-patrones prohibidos

```bash
# ❌ Editar la versión a mano en README/config/llms (drift → falla el check 19)
# ❌ Tocar feed/advisories.json fuera de --release-feed (firma stale)
# ❌ Lanzar --yes a ciegas sin --dry-run previo cuando hay dudas
# ❌ Releasear con la sección del CHANGELOG vacía o con marcadores pendientes
# ❌ Forzar el release tras un fallo de auditoría en vez de corregirlo
```

## Cross-references
- Para la ceremonia de claves y firma minisign + ML-DSA-65 → ver `signing/SKILL.md`
- Para el feed de actualizaciones firmado → ver `updates/SKILL.md`
- Para cabeceras/CHANGELOG antes del release → ver `docs-update/SKILL.md`
- Para la auditoría que actúa de gate → ver `security/SKILL.md`
