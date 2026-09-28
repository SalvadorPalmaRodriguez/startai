# Licencias de terceros

> **Documento de proceso** (desarrollador). El artefacto generado que se publica
> junto al proyecto es `THIRD_PARTY_LICENSES.txt` (en inglés).
>
> **Nota:** `{{product_name}}` no tiene dependencias de terceros en tiempo de
> ejecución por defecto (este scaffold usa solo la biblioteca estándar); este
> fichero documenta la política a aplicar cuando se añadan dependencias.

Este documento explica **cómo generar y mantener** el aviso de licencias de
terceros para un proyecto con **licencia propietaria de código visible**
(ver [`LICENSE`](LICENSE)). El software propio es propietario; las dependencias
de terceros conservan sus licencias originales y deben listarse.

---

## Por qué es obligatorio

- El código del proyecto es **propietario**, pero casi siempre usa librerías
  de terceros (MIT, Apache-2.0, BSD, ISC, etc.).
- Publicar el código sin declarar esas licencias es un **incumplimiento** de la
  mayoría de ellas (muchas exigen incluir su texto de copyright/aviso).
- Un aviso completo es, además, una señal de **madurez y transparencia** para
  quien audite o compile el proyecto.

## Qué contiene el aviso

1. **Cabecera** — nombre del proyecto, fecha de generación y nota de que el
   software propio es propietario (ver `LICENSE`).
2. **Lista completa de dependencias** — paquete, versión y licencia (SPDX).
3. **Textos de licencia** — el texto completo de cada licencia distinta
   (MIT, Apache-2.0, BSD-2/3-Clause, etc.) para cumplir el requisito de
   redistribución del aviso.

## Cómo generarlo (según ecosistema)

| Ecosistema | Herramienta | Comando de ejemplo |
|------------|-------------|--------------------|
| Rust / Cargo | `cargo-about` o `cargo-deny` | `cargo about generate about.hbs > THIRD_PARTY_LICENSES.txt` |
| Node / npm | `license-checker` / `npm-license-crawler` | `license-checker --csv` |
| Python | `pip-licenses` | `pip-licenses --format=plain-vertical` |
| Java / Maven | `license-maven-plugin` | `mvn license:aggregate-third-party-report` |
| Go | `go-licenses` | `go-licenses report ./...` |

> La lista debe generarse **a partir del lockfile** (`Cargo.lock`,
> `package-lock.json`, `requirements.txt`, `pom.xml`, `go.sum`), nunca a mano.

## Reglas de mantenimiento

- **Regenerar** el aviso en cada release y cuando cambien las dependencias.
- **No** mezclar el aviso de terceros con la licencia del proyecto: van en
  ficheros separados (`LICENSE` vs `THIRD_PARTY_LICENSES.*`).
- **Auditar** incompatibilidades: si una dependencia es copyleft (GPL/AGPL) y el
  proyecto es propietario, evaluar su reemplazo o segregación.
- Guardar el fichero generado con un nombre estable y versionado.

## Ejemplo de cabecera del fichero generado

```
================================================================================
  {{product_name}} — THIRD-PARTY SOFTWARE LICENSE NOTICES
  Generated: YYYY-MM-DD
================================================================================

This file lists all third-party software dependencies used in the
{{product_name}} project, along with their license information.

The {{product_name}} software itself is proprietary. See the LICENSE file
for details. The third-party components listed below retain their
original licenses.
```

---

Ver también: `.agents/skills/license/SKILL.md` · [`docs/es/license.md`](docs/es/license.md) · [`docs/en/license.md`](docs/en/license.md).
