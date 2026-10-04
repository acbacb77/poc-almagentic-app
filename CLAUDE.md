@AGENTS.md

## Específico de Claude Code

- Los permisos, el hook `.claude/hooks/guard.py` y el sandbox aplican las reglas de arriba. Si algo se bloquea, es intencionado: no busques un rodeo, explica en el PR qué necesitabas.
- Para una feature nueva usa las skills de Spec Kit en orden: `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` y después `/speckit-implement`. `/speckit-clarify` y `/speckit-analyze` son opcionales.
- Las skills de Spec Kit (`.claude/skills/speckit-*`) y sus plantillas y scripts (`.specify/`) son parte del harness: úsalas, no las modifiques.
- Al terminar, abre el PR con `gh pr create` usando la plantilla del repo.
