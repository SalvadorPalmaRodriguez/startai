# Memory (persistente)

<!-- >>> startai:if-ai-private >>>
Memoria a largo plazo del orquestador — a diferencia de `state/`, este
directorio SÍ se conserva entre sesiones (sigue siendo privado: todo
`.agents/` está gitignored).
<!-- <<< startai:endif <<<
<!-- >>> startai:if-ai-public >>>
Memoria a largo plazo del orquestador — a diferencia de `state/`, este
directorio SÍ se conserva entre sesiones (y se versiona: `.agents/` es
público en este proyecto).
<!-- <<< startai:endif <<<

- `decisions.md` — registro de decisiones (fecha, decisión, contexto,
  consecuencias).
- `roadmap.md` — hoja de ruta viva que el orquestador consulta al planificar.
