---
name: ccaa-commit-push
description: Commits and pushes CCAA (Consumer Complaints Agentic App) work as the repository owner after lint and tests pass. Use after every plan task or sub-task of a story, at the logical end of a story, and when the user runs /ccaa-commit-push.
---

# ccaa-commit-push

Input: optional story issue number `N` (`/ccaa-commit-push 55`). Without it, use the story started in this chat (`/ccaa-story-start`); if there is none, ask which story the change belongs to, or use the `M02: <summary>` form for work not tied to one story.

Commit small and often: after each plan task, each passing test with its code, each migration, each document change, and at the end of every story. One logical change per commit.

0. With `N`, read the key: `gh issue view N --json title` (the `M02-00NN` at the start of the title).
1. `git status -s`. Stage only the files this change touched, by name. Never `git add -A` or `git add .`. Never stage datasets (`*.csv`, `*.zip`), `.env` files, secrets or `runtime_data/`. If a `docs/Project_Management/Issues/Milestone_*.md` is modified (a `ccaa-milestone-log` change), stage it too. Stage the story's spec and plan files in `docs/Superpowers/` as well.
2. If Python code changed, run `npm run local:api:lint` and `npm run local:api:test` from the repo root. Do not commit on a failure.
3. Commit with a single-line message (no body): `M02-00NN #N: <imperative summary>`. The key `M02-00NN` is at the start of the story title. For work not tied to one story use `M02: <summary>`.
4. The author must be the repository owner as set in `git config user.name` and `git config user.email` (check them), never Cursor or any AI. Do not pass `--author` and do not change `git config`.
5. Cursor's git wrapper may add a `Co-authored-by` trailer. Check with `git log -1 --format='%an <%ae>%n%B'`. If the body has any `Co-authored-by`, `cursoragent@cursor.com` or other AI trailer, rebuild the commit before pushing:
   ```bash
   NEW=$(git commit-tree "$(git rev-parse 'HEAD^{tree}')" -p HEAD^ -m "$(git log -1 --format=%s)")
   git update-ref "refs/heads/$(git branch --show-current)" "$NEW"
   ```
   Then check the log again.
6. `git push origin "$(git branch --show-current)"`. If rejected, `git pull --rebase origin "$(git branch --show-current)"`, then push again.
7. Confirm with `git status -sb` that the branch is not ahead. Report the short hash and subject.
