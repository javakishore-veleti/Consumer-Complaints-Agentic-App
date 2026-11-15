# Consumer-Complaints-Agentic-App

> [!CAUTION]
> # Install Superpowers on your laptop
> **To truly use this repo’s Superpowers integration (structured agent workflows: brainstorm → plan → TDD → review), each developer must install the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor on their machine.**
>
> In Cursor, run:
> ```text
> /add-plugin superpowers
> ```
> Workspace setting `.cursor/settings.json` only *enables* the plugin for this project — it does **not** ship the skills in git.
>
> **The application still runs without Superpowers.** Middleware, Admin portal, Airflow, migrations, and tests work with the npm/local scripts below. Superpowers is for AI-assisted *development process*, not runtime.

## Development tooling

### Local containers (lite profiles)

Default local path uses **SQLite** for the operational/admin store — **no operational Postgres container**. Start Airflow only:

```bash
npm run local:containers:sqlite:start    # Airflow (SQLite-lite default)
npm run local:containers:sqlite:status   # shows expected: airflow
```

Opt-in profiles:

```bash
npm run local:containers:postgres:start  # Airflow + CCA operational Postgres
npm run local:containers:mongodb:start   # Airflow + MongoDB
```

`npm run local:containers:all:*` still starts/stops/status **every** `CICD/Local/*/docker-compose.yaml`. **Stop always removes Docker volumes** (`docker compose down -v`) so Airflow/Mongo/Postgres data does not linger (M01-0073 / #133). Pass `--keep-volumes` to `CICD/Local/docker-all-down.sh` only when you intentionally want to keep them. For Postgres/Mongo app config, set `.env` per `Middleware/ConsumerComplaintsHandsOn/.env.example` (D75–D78).

### Recommended local stack (three steps)

```bash
npm run local:containers:all:start          # or :sqlite:start / :postgres:start / :mongodb:start
npm run local:handson:middlware:all:start   # Middleware API (:8000)
npm run local:portals:all:start             # all Portals apps (today: admin on :4200)
```

`local:portals:all:*` is the umbrella for every app under `Portals/`; add future portals there. `local:portals:all:start` always runs `npm install` in the admin portal first (so pulls never leave deps stale), then `ng serve`. Single-app shortcuts remain: `local:portal:admin:start|build|test`. Shortcut `local:portal:admin:with-api` still starts Middleware then `local:portals:all:start`.

Admin Angular needs **Node.js 22+** (see root `.nvmrc`). If `nvm` defaults to 20:

```bash
nvm use    # or: nvm use 22
npm run local:portals:all:start
```

Then open http://localhost:4200/datasets/imports.

E2E happy path (UI → API → Airflow → callback → UI, SQLite first): see `docs/local-admin-e2e-happy-path.md`. CI smoke: `npm run local:e2e:happy-path:smoke`. Live API probe: `npm run local:e2e:happy-path:probe`. DoD matrix (SQLite / Postgres / MongoDB): `docs/local-admin-e2e-dod-matrix.md` · `npm run local:e2e:dod-matrix:smoke`.

### Superpowers plugin

> [!IMPORTANT]
> Superpowers is **required for the agent workflow** documented here, but **optional for running the product**. See the red **CAUTION** banner at the top of this README.

This project uses the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor (install on **your laptop**, not vendored into this repo). It is a core skills library that gives the AI agent structured workflows for development tasks.

Skills included:

- **Planning and design:** `brainstorming`, `writing-plans`, `executing-plans`
- **Building and testing:** `test-driven-development`, `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`
- **Debugging and quality:** `systematic-debugging`, `verification-before-completion`
- **Code review and wrap-up:** `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`
- **Meta:** `using-superpowers`, `writing-skills`

A `sessionStart` hook loads the `using-superpowers` skill at the start of each session, so the agent checks for a relevant skill before it acts.

To install it in Cursor, run:

```
/add-plugin superpowers
```

Invoke a skill directly with `/`, for example `/brainstorming`. The agent also uses skills automatically when they apply.

#### The basic workflow

See [The Basic Workflow](https://github.com/obra/superpowers#the-basic-workflow) in the Superpowers README. In short:

1. **brainstorming:** Runs before building anything. It draws out what you want and why, then plays its understanding back for correction.
2. **using-git-worktrees:** Runs after design approval. It creates an isolated workspace on a new branch and verifies a clean test baseline.
3. **writing-plans:** Breaks the approved design into small tasks (2-5 minutes each), with exact file paths and verification steps.
4. **subagent-driven-development** or **executing-plans:** Runs the plan, either with a fresh subagent and review per task, or inline with one review of the whole branch at the end.
5. **test-driven-development:** Enforces RED-GREEN-REFACTOR during implementation.
6. **requesting-code-review:** Reviews work against the plan between tasks and reports issues by severity.
7. **finishing-a-development-branch:** Verifies tests and presents merge, PR, keep or discard options.

The agent checks for relevant skills before any task, so these workflows are mandatory rather than optional.
