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

## Pedir algo

1. Abre un issue con la plantilla **Petición**: qué necesitas, para quién, qué se gana y la urgencia.
2. En un par de minutos, el agente de triage comenta una **propuesta**: tipo, prioridad, tamaño, criterios de aceptación, preguntas abiertas y posibles duplicados, y pone las etiquetas `tipo:*`, `prioridad:*`, `tamano:*` y `triage:propuesto`.
3. Un responsable revisa y decide:
   - **De acuerdo:** añade la etiqueta `aprobado`. Es la señal para que el agente escriba la spec (tarea 4).
   - **No del todo:** cambia las etiquetas o comenta lo que falta.
   - **Repetir el triage** tras editar la petición: añade `triage:repetir`.

Las peticiones de personas sin acceso al repo no pasan por el agente: reciben `triage:manual`. Si la propuesta lleva `triage:sospechoso`, el texto parecía contener instrucciones para el agente: revísala con cuidado.

## Arrancar el agente

1. **Clave de la App, una sola vez.** Copia la clave privada de `almagentic-agent` a `~/.config/almagentic/agent/agent.pem` en tu máquina. Si el repo está en el disco de Windows (también si lo abres desde `/mnt/c` en WSL), la ruta es `%USERPROFILE%\.config\almagentic\agent\agent.pem`. Nunca dentro de un repo, y sin otras claves en esa carpeta: se monta entera en el contenedor.
2. Abre el repo en VS Code y elige **Reopen in Container**. El contenedor monta esa carpeta en solo lectura y trae Python 3.12, uv, GitHub CLI y Claude Code.
3. En el terminal del contenedor:
   ```bash
   .devcontainer/start-agent.sh
   ```
   El script obtiene un token de la App válido 1 hora y solo para este repo, y arranca `claude` como `almagentic-agent[bot]`. Cuando caduque, sal y vuelve a lanzarlo.

No definas `ANTHROPIC_API_KEY` en el contenedor: Claude Code usará tu suscripción.

## El harness del agente

| Capa | Dónde | Qué impone |
|---|---|---|
| Contexto | `AGENTS.md`, `CLAUDE.md` | Cómo trabajar y qué no tocar |
| Constitución | `.specify/memory/constitution.md` | Principios que Spec Kit aplica a cada spec |
| Permisos | `.claude/settings.json` | Qué ejecuta sin preguntar, qué pregunta y qué tiene prohibido |
| Hook | `.claude/hooks/guard.py` | Bloquea rutas protegidas, push a main y secretos; registra cada bloqueo en `.claude/audit/` |
| Sandbox | `.claude/settings.json` → `sandbox` | Red limitada a GitHub y PyPI; sin lectura de `/run/secrets` |
| Identidad | GitHub App `almagentic-agent` | Token de 1 hora, sin permiso para `.github/workflows/` |
| Plataforma | CODEOWNERS + ruleset de `main` | PR obligatorio y aprobación humana |

El estándar común vive en [poc-almagentic-core/agent-standards](https://github.com/acbacb77/poc-almagentic-core/tree/main/agent-standards); la versión usada aquí está en `.agent-standards-version`.

Si el sandbox no arranca en tu Docker (Claude Code se niega a iniciar), crea `.claude/settings.local.json` con `{"sandbox": {"failIfUnavailable": false}}` y avísalo: perderás la capa de red, no las demás.

## Spec Kit

El repo incluye [GitHub Spec Kit](https://github.com/github/spec-kit) v1.1.0 para el desarrollo guiado por especificaciones: las skills `/speckit-*` en `.claude/skills/` y las plantillas y scripts en `.specify/`. Los ficheros están versionados, así que el agente no necesita instalar nada. Son parte del harness: el agente no puede editarlos y cualquier cambio pasa por revisión humana (CODEOWNERS).

Para actualizar a otra versión (lo hace una persona, en una rama propia):

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init --here --force --integration claude --script sh
```

Después revisa el diff: `specify init` no debe tocar `.specify/memory/constitution.md`, `CLAUDE.md` ni `.claude/settings.json`.
