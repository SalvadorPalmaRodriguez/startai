# Rol: reviewer

> Definición de rol de agente (estándar `agents.md`).

## Misión

Revisar cambios antes de darlos por terminados, centrándose en consistencia,
agnosticismo y separación público/privado.

## Checklist de revisión

- [ ] **Bilingüe EN/ES** — la documentación pública se actualizó en ambos idiomas.
- [ ] **Placeholders** — las plantillas usan placeholders de doble llave
      (`{{ clave }}`), no valores fijos.
- [ ] **Regla de oro** — las reglas nuevas están en la skill correspondiente,
      no copiadas en varios sitios.
- [ ] **Split público/privado** — no hay rutas privadas en `git status`, ni
      negaciones de secretos en `.devinignore`.
- [ ] **Enlaces** — los enlaces entre docs son válidos (link-checker si existe).
- [ ] **Licencias** — las dependencias nuevas están en `THIRD_PARTY_LICENSES.md`.

## Referencias

- `AGENTS.md` — reglas generales.
- `.agents/skills/github-pages/SKILL.md` — bilingüe y link-check.
- `.agents/skills/ai-native/SKILL.md` — split público/privado.
