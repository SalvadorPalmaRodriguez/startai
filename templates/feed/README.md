# feed/ — Feed de actualizaciones firmado de {{product_name}}

`advisories.json` es el índice firmado con minisign que permite a los usuarios
comprobar si hay una versión nueva de {{product_name}} **de forma verificable**.
El esquema completo y el protocolo están descritos en
`.agents/skills/updates/SKILL.md`.

## Claves (generar UNA vez)

```bash
minisign -G -p feed/minisign.pub -s feed/minisign.key
```

- `feed/minisign.pub` — **pública**: se versiona (y/o se embebe en el
  artefacto como trust anchor).
- `feed/minisign.key` — **privada**: NUNCA se versiona. Está cubierta por el
  patrón `*.key` del `.gitignore`; mejor aún, muévela fuera del repo
  (`~/.minisign/`).

## Tras cada release

`scripts/dev/release.sh` ya ejecuta estos pasos (vía
`scripts/dev/sync_version.sh --release-feed`). A mano serían:

1. Actualiza `latest`, `download_url` y `published_at` en `advisories.json`
   (revisa también `min_supported`, `severity_summary` y `advisories`).
2. Re-firma el feed:
   ```bash
   minisign -Sm feed/advisories.json -x feed/advisories.json.minisig
   ```
3. Publica `feed/` con el sitio estático del proyecto (o como assets del
   repo/release) junto al `.minisig`.

## Verificación offline (usuario)

```bash
minisign -Vm feed/advisories.json -p feed/minisign.pub
# o con la clave pública como string:
minisign -Vm feed/advisories.json -P <pubkey>
```

> Si el proyecto aún no usa feed de actualizaciones, este directorio es
> opcional: puede eliminarse o mantenerse como esqueleto.
