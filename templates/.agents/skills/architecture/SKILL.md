---
name: architecture
description: Generic engineering guidelines for any project built with AI agents — hexagonal architecture as recommended reference, SOLID principles, structured errors and mandatory tests, language-agnostic
---

# Architecture

## Cuándo usar esta skill
- Crear o modificar código en cualquier capa del proyecto.
- Decidir dónde vive una pieza de lógica nueva (regla de negocio, I/O, orquestación).
- Añadir una dependencia externa o un punto de entrada (CLI, API, UI).

## Arquitectura hexagonal (referencia recomendada)

```
domain/         → Lógica pura de negocio. SIN dependencias externas ni I/O.
ports/          → Interfaces/contratos (puertos) que el dominio y la
                  aplicación necesitan del exterior.
adapters/       → Implementaciones concretas de los puertos (BBDD, HTTP,
                  ficheros, servicios externos).
application/    → Casos de uso / orquestación. Depende SOLO de ports,
                  NUNCA de adapters.
interfaces/     → Capa de entrada (CLI, API, UI). Solo routing y validación;
                  traduce errores y delega en application.
```

**Regla inviolable:** la capa de aplicación importa contratos (ports), nunca
implementaciones (adapters). Las dependencias siempre apuntan hacia el dominio.

Si el proyecto usa otra arquitectura, el nombre concreto es `{{architecture}}`
y debe respetar los mismos principios de dirección de dependencias.

## Principios SOLID (agnósticos de lenguaje)

- **S** — Responsabilidad única: un módulo/caso de uso = una razón para cambiar.
- **O** — Abierto/cerrado: extender comportamiento sin modificar lo existente.
- **L** — Sustitución: cualquier implementación de un puerto debe poder
  sustituir a otra sin romper al cliente.
- **I** — Segregación de interfaces: puertos pequeños, orientados al cliente
  que los consume.
- **D** — Inversión de dependencias: depender de abstracciones (ports), no de
  detalles (adapters).

## Errores

- Errores **tipados/estructurados** en `domain/` y `application/` (tipos de
  error propios, no strings sueltos).
- El boundary (CLI/API/main) traduce los errores del dominio a mensajes de
  usuario, códigos de salida o respuestas HTTP.
- **PROHIBIDO** tragarse errores en silencio (`catch` vacío, ignorar un
  `Result`/`error` devuelto, log sin propagación).

## Tests

- **Obligatorios** para toda lógica de `domain/` y `application/`.
- Los puertos facilitan mocks/fakes: los tests de aplicación no tocan I/O real.
- Visibilidad mínima en todo símbolo; prefieren referencias sobre copias
  (`&`/`[]`/vistas) donde el lenguaje lo permita.

## Anti-patrones prohibidos

```
# ❌ Importar un adapter desde application/ (saltarse el puerto)
# ❌ Lógica de negocio dentro de un adapter o de la capa de entrada
# ❌ Dependencia externa (framework, red, FS) importada en domain/
# ❌ tragar errores o devolver códigos de error mágicos sin tipo
# ❌ unwrap()/panic()/exit() en lógica de dominio o aplicación
```

## Cross-references
- Para las reglas mínimas operativas → ver `AGENTS.md` §3
- Para el split público/privado de ficheros → ver `ai-native/SKILL.md`
