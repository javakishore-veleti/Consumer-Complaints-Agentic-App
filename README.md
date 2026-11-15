# Consumer-Complaints-Agentic-App

## Development tooling

### Admin portal

Angular app at `Portals/consumer-complaints-admin/` (Node 22+). One-command local UI + Middleware:

```bash
npm run local:portal:admin:with-api
```

Then open http://localhost:4200/datasets/imports. Portal-only: `npm run local:portal:admin:start` (API must already be on `127.0.0.1:8000`).

### Superpowers plugin

This project uses the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor. It is a core skills library that gives the AI agent structured workflows for development tasks.

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
