# Consumer-Complaints-Agentic-App

## Development tooling

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
