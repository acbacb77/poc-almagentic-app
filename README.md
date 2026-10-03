# poc-almagentic-app

API REST de ejemplo (Python/FastAPI) para la POC de **ALM agéntico**.
Es el único repo en el que el agente de código (Claude Code) tiene permiso de escritura, siempre a través de PRs revisados por un humano.

## Repos de la POC

| Repo | Qué contiene | Quién escribe |
|---|---|---|
| **poc-almagentic-app** (este) | Código, specs y harness del agente | El agente, con PRs revisados |
| [poc-almagentic-core](https://github.com/acbacb77/poc-almagentic-core) | Workflows reutilizables y estándares de agentes | Solo humanos |
| [poc-almagentic-gitops](https://github.com/acbacb77/poc-almagentic-gitops) | Estado deseado del cluster (Argo CD) | Un bot abre PRs, un humano aprueba |

## Estructura (se completa tarea a tarea)

```
AGENTS.md                # contexto y reglas del agente (tarea 3)
CLAUDE.md                # importa AGENTS.md para Claude Code (tarea 3)
.claude/settings.json    # comandos permitidos y denegados (tarea 3)
.specify/memory/         # constitución de Spec Kit (tarea 3)
specs/                   # specs de cada feature (tarea 4)
.devcontainer/           # entorno aislado para el agente (tarea 2)
.github/
  CODEOWNERS             # zonas que exigen aprobación humana (tarea 2)
  ISSUE_TEMPLATE/        # entrada de demanda (tarea A)
  workflows/             # llamadas a los workflows de core (tareas 6-10, B)
src/app/                 # la API (tarea 5)
tests/                   # tests (tarea 5)
evals/                   # pruebas del harness al cambiar de modelo (tarea C)
```

## Trabajar en local

Abre el repo en VS Code y elige **Reopen in Container**. El contenedor trae Python 3.12, GitHub CLI y Claude Code.
No definas `ANTHROPIC_API_KEY` dentro del contenedor: Claude Code usará tu suscripción al iniciar sesión con `claude`.
