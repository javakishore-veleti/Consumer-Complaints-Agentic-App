---
name: ccaa-story-start
description: Marks a CCAA (Consumer Complaints Agentic App) GitHub story as started and refreshes its parent feature and epic. Use when the user runs /ccaa-story-start N before working on story issue N.
disable-model-invocation: true
---

# ccaa-story-start

Input: story issue number `N`. Run `gh` from the repository root: it reads the repository from the git remote, so never type the owner or repository name (D35). Needs network access.

Scratch files go in `runtime_data/tmp/` (git-ignored), never `/tmp`.

1. `gh issue view N --json title,state,labels,body`. Stop and tell the user if the title has no `[Story]` or the issue is closed.
2. Labels: `gh issue edit N --remove-label "status: planned" --add-label "status: in-progress"`.
3. Body: replace the `**Status:**` line with `**Status:** In progress — started YYYY-MM-DD.` (use `date +%F`). Change nothing else. Save to `runtime_data/tmp/issue-N.md`, then `gh issue edit N --body-file runtime_data/tmp/issue-N.md`.
4. Read `**Epic:** #E · **Feature:** #F` from the body. For each of `F` and `E` that still has `status: planned`, swap it for `status: in-progress`.
5. Run `ccaa-progress-sync` on `F`, then on `E`.
6. Log it in the milestone file: `ccaa-milestone-log N begin`, then `ccaa-milestone-log N` (step 1, this command, is done and step 2 starts). Also run `ccaa-milestone-log F begin` (and `E`) if step 4 just moved it from planned to in-progress.
7. Run `ccaa-commit-push N` with the summary `start story`.
8. Reply with the story title and the next command from the `In progress` row of `docs/Project_Management/Issues/Milestone_02.md`.

For the rest of this chat, after each workflow step of story `N` finishes (brainstorming, using-git-worktrees, writing-plans, test-driven-development, the final task of subagent-driven-development and its commit, verification, code review, the final `ccaa-commit-push N`, finishing-a-development-branch), run `ccaa-milestone-log N` before you suggest the next command.

This step runs on `main`. The next steps run in the story's worktree and branch (`/using-git-worktrees` creates both in `.worktrees/`).
