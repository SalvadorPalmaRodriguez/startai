# Orchestrator (opcional)

Contrato de directorios para un orquestador de agentes externo: lee
`AGENTS.md`, las skills y los roles, ejecuta `workflows/` declarativos y
mantiene `memory/` y `state/`. Todo bajo `.agents/` es privado (gitignored).

- `config.yaml` — contrato: rutas de conocimiento, skills, roles, workflows.
- `roles/` — quién hace qué (architect, developer, reviewer, security, tester).
- `workflows/` — flujos declarativos (bugfix, feature, review).
- `memory/` — memoria persistente entre sesiones (decisiones, roadmap).
- `state/` — estado temporal de la sesión (no se conserva).

No es obligatorio: si el proyecto no usa un orquestador, este directorio se
puede borrar sin tocar nada más.
