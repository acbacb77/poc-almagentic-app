@AGENTS.md

## Específico de Claude Code

- Los permisos, el hook `.claude/hooks/guard.py` y el sandbox aplican las reglas de arriba. Si algo se bloquea, es intencionado: no busques un rodeo, explica en el PR qué necesitabas.
- Para una feature nueva usa los comandos de Spec Kit en orden: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks` y después `/speckit.implement`.
- Al terminar, abre el PR con `gh pr create` usando la plantilla del repo.
