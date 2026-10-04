# feed/ — Feed de actualizaciones firmado de startai

`advisories.json` es el índice firmado con minisign que permite a los usuarios
comprobar si hay una versión nueva de startai **de forma verificable**. El
esquema completo y el protocolo están descritos en la skill `updates`.

## Piezas

| Fichero | Rol | ¿Versionado? |
|---------|-----|--------------|
| `advisories.json` | Índice de versiones y advisories | Sí |
| `advisories.json.minisig` | Firma minisign del índice | Sí |
| `minisign.pub` | Clave pública del feed | Sí (y/o embebida en el artefacto) |
| `~/.minisign/startai-feed.key` | Clave **privada** del feed | **NUNCA** |

La clave del feed es **independiente** de la clave de firma de artefactos
(`~/.minisign/startai.key`) — mismo modelo que enola-cli-lite.

## Generar las claves (una sola vez)

```bash
minisign -G -p feed/minisign.pub -s ~/.minisign/startai-feed.key
```

## Tras cada release

`scripts/dev/release.sh` ejecuta `sync_version.sh --release-feed`; para que use
la clave separada, lanzar con la variable de entorno:

```bash
FEED_MINISIGN_KEY=~/.minisign/startai-feed.key bash scripts/dev/release.sh --yes
```

A mano serían:

```bash
# 1. actualizar latest / download_url / published_at en advisories.json
# 2. re-firmar
minisign -S -s ~/.minisign/startai-feed.key -m feed/advisories.json -x feed/advisories.json.minisig
# 3. verificar antes de publicar
minisign -V -m feed/advisories.json -x feed/advisories.json.minisig -p feed/minisign.pub
# 4. publicar feed/ con el sitio estático (docs/feed/ → GitHub Pages)
```

## Verificación offline (usuario)

```bash
minisign -Vm feed/advisories.json -p feed/minisign.pub
# o con la clave pública como string:
minisign -Vm feed/advisories.json -P <pubkey>
```

Solo después de una verificación OK se confía en `latest` y `download_url`.

## Roadmap

El campo `milestones` de `advisories.json` lleva el roadmap público del
proyecto (mismo patrón que `pqc_milestones` en enola-cli-lite). Se rellena y
re-firma con cada release.