# Memory (persistente)

Memoria a largo plazo del orquestador — a diferencia de `state/`, este
directorio SÍ se conserva entre sesiones (sigue siendo privado: todo
`.agents/` está gitignored).

- `decisions.md` — registro de decisiones (fecha, decisión, contexto,
  consecuencias).
- `roadmap.md` — hoja de ruta viva que el orquestador consulta al planificar.
