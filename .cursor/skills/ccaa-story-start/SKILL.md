---
name: ccaa-story-start
description: Marks a CCAA (Consumer Complaints Agentic App) GitHub story as started and refreshes its parent feature and epic. Use when the user runs /ccaa-story-start N before working on story issue N.
disable-model-invocation: true
---

# ccaa-story-start

Input: story issue number `N`. Run `gh` from the repository root: it reads the repository from the git remote, so never type the owner or repository name (D35). Needs network access.

**Hard gate reminder:** Creating a GitHub `[Story]` issue is **not** permission to edit product code. Product edits (`Middleware/`, `Portals/`, DAGs, migrations, feature tests) are forbidden until **this skill finishes** for `N` **and** the user asked to start that story. No exceptions.

Scratch files go in `runtime_data/tmp/` (git-ignored), never `/tmp`.

1. `gh issue view N --json title,state,labels,body,milestone`. Stop and tell the user if the title has no `[Story]` or the issue is closed.
1a. **Hard gate — GitHub Milestone required.** If `milestone` is `null`, **STOP**. Do not change labels, body, milestone log, or code. Tell the user to create the GitHub Milestone (repo → Milestones) and attach issue `N` (`gh issue edit N --milestone "<title>"`), then re-run `/ccaa-story-start N`. A `docs/Project_Management/Issues/Milestone_*.md` file alone is not enough.
1b. If product files are already modified on `main` without this story having been started: **STOP** after board updates in this skill; tell the user the gate was violated and ask whether to discard WIP or continue only after Superpowers worktree steps — do not keep editing product code in the same breath as story-start.
2. Labels: `gh issue edit N --remove-label "status: planned" --add-label "status: in-progress"`.
3. Body: replace the `**Status:**` line with `**Status:** In progress — started YYYY-MM-DD HH:MM.` (use `date '+%F %H:%M'`). Change nothing else. Save to `runtime_data/tmp/issue-N.md`, then `gh issue edit N --body-file runtime_data/tmp/issue-N.md`.
4. Read `**Epic:** #E · **Feature:** #F` from the body. For each of `F` and `E` that still has `status: planned`, swap it for `status: in-progress`.
5. Run `ccaa-progress-sync` on `F`, then on `E`.
6. Log it in the milestone file: `ccaa-milestone-log N begin`, then `ccaa-milestone-log N` (step 1, this command, is done and step 2 starts). Also run `ccaa-milestone-log F begin` (and `E`) if step 4 just moved it from planned to in-progress.
7. Run `ccaa-commit-push N` with the summary `start story`.
8. Reply with the story title and the next command from the `In progress` row of the matching `docs/Project_Management/Issues/Milestone_MM.md` (from the issue title prefix `M02` / `M03` / …).

For the rest of this chat, after each workflow step of story `N` finishes (brainstorming, using-git-worktrees, writing-plans, test-driven-development, the final task of subagent-driven-development and its commit, verification, code review, the final `ccaa-commit-push N`, finishing-a-development-branch), run `ccaa-milestone-log N` before you suggest the next command.

This step runs on `main`. The next steps run in the story's worktree and branch (`/using-git-worktrees` creates both in `.worktrees/`).

**After this skill:** do **not** jump to implementation. Announce the next Superpowers step from the milestone table (usually brainstorming or using-git-worktrees) and wait for / follow that skill. Product code changes only inside the worktree after the plan/TDD steps say so.
