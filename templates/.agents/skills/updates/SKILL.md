---
name: updates
description: Signed update feed with minisign — advisories.json schema, re-signing on every release, static publication, and offline verification by users
---

# Updates — feed de actualizaciones firmado

## Cuándo usar esta skill
- Publicar una release y mantener el feed de actualizaciones del proyecto.
- Implementar la comprobación de "hay versión nueva" en el cliente/instalador.
- Generar o rotar la clave minisign que firma el feed.

## Qué es

`feed/advisories.json` es un **índice JSON firmado con minisign** que permite a
los usuarios del proyecto comprobar si hay una versión nueva **de forma
verificable**: el cliente descarga el feed, verifica la firma con la clave
pública y solo entonces confía en su contenido (`latest`, `download_url`).

Piezas del sistema:

| Fichero | Rol | ¿Versionado? |
|---------|-----|--------------|
| `feed/advisories.json` | Índice de versiones y advisories | Sí |
| `feed/advisories.json.minisig` | Firma minisign del índice | Sí |
| `feed/minisign.pub` | Clave pública del feed | Sí (y/o embebida en el artefacto) |
| `feed/minisign.key` | Clave **privada** del feed | **NUNCA** |

Si el proyecto aún no implementa feed de actualizaciones, el directorio
`feed/` es **opcional**: puede eliminarse o mantenerse como esqueleto hasta
la primera release.

## Esquema de `feed/advisories.json`

| Campo | Significado |
|-------|-------------|
| `schema_version` | Versión del formato del feed (string, `"1"`) |
| `latest` | Última versión publicada |
| `min_supported` | Versión mínima soportada; las anteriores deben actualizar |
| `download_url` | URL de descarga de la release actual |
| `published_at` | Timestamp ISO-8601 UTC de publicación (`YYYY-MM-DDThh:mm:ssZ`) |
| `docs_url` | URL de la documentación del proyecto |
| `severity_summary` | Conteo de advisories por severidad (`critical`, `high`, `medium`, `low`) |
| `signature_urls` | Mirrors donde descargar el `.minisig` del feed |
| `advisories` | Lista de avisos (vulnerabilidades, actualizaciones críticas) |
| `enforce_updates` | Si `true`, el cliente puede exigir la actualización |

## Flujo de release

Al publicar una release (la ceremonia completa de firma de artefactos vive en
`signing/SKILL.md` — el feed es el **índice firmado que apunta a esos
artefactos**). Los pasos 1–2 están automatizados por
`scripts/dev/sync_version.sh --release-feed`, que `scripts/dev/release.sh`
ejecuta dentro del pipeline:

1. Actualizar en `feed/advisories.json`: `latest`, `download_url`,
   `published_at`; revisar `min_supported`, `severity_summary` y `advisories`.
2. Re-firmar el feed:
   ```bash
   minisign -Sm feed/advisories.json -x feed/advisories.json.minisig
   ```
3. Verificar la firma antes de publicar:
   ```bash
   minisign -Vm feed/advisories.json -p feed/minisign.pub
   ```
4. Publicar `feed/` con el sitio estático del proyecto (p. ej. copiarlo a
   `docs/feed/` para GitHub Pages → `https://{{github_user}}.github.io/{{repo}}/feed/`)
   o como assets del repo/release. El `.minisig` debe acompañar siempre al
   JSON; los mirrors van en `signature_urls`.
5. Commitear `feed/advisories.json` + `advisories.json.minisig` junto con la
   release — el feed y su firma viajan en el mismo commit/tag.

## Claves del feed

Generar el par de claves UNA vez (ver `feed/README.md`):

```bash
minisign -G -p feed/minisign.pub -s feed/minisign.key
```

- `feed/minisign.pub` — pública. Se versiona y/o se embebe en el artefacto
  como trust anchor.
- `feed/minisign.key` — privada. **NUNCA se versiona**: el patrón `*.key`
  del `.gitignore` ya la cubre, pero lo recomendable es guardarla fuera del
  repo (`~/.minisign/`) con passphrase — igual que la clave de firma de
  releases (ver `signing/SKILL.md`).

## Verificación offline por el usuario

```bash
# Con el fichero de clave pública:
minisign -Vm feed/advisories.json -p feed/minisign.pub

# Con la clave pública como string:
minisign -Vm feed/advisories.json -P <pubkey>
```

Solo después de una verificación OK se confía en `latest` y `download_url`.
Un cliente automático debe abortar la actualización si la firma no verifica.

## Anti-patrones prohibidos

```
# ❌ Actualizar advisories.json sin re-firmar (firma stale = feed inválido)
# ❌ Commitear feed/minisign.key o cualquier *.key
# ❌ Editar latest/download_url fuera del flujo de release
# ❌ Confiar en el feed sin verificar la firma primero (cliente o usuario)
# ❌ Publicar el JSON sin su .minisig
```

## Cross-references
- Para la firma de los artefactos de release → ver `signing/SKILL.md`
- Para servir `feed/` desde el sitio estático → ver `github-pages/SKILL.md`
