---
name: ccaa-story-start
description: Marks a CCAA (Consumer Complaints Agentic App) GitHub story as started and refreshes its parent feature and epic. Use when the user runs /ccaa-story-start N before working on story issue N.
disable-model-invocation: true
---

# ccaa-story-start

Input: story issue number `N`. Repo: `javakishore-veleti/Consumer-Complaints-Agentic-App` (pass `--repo` to every `gh` call). Needs network access.

Scratch files go in `runtime_data/tmp/` (git-ignored), never `/tmp`.

1. `gh issue view N --json title,state,labels,body`. Stop and tell the user if the title has no `[Story]` or the issue is closed.
2. Labels: `gh issue edit N --remove-label "status: planned" --add-label "status: in-progress"`.
3. Body: replace the `**Status:**` line with `**Status:** In progress — started YYYY-MM-DD.` (use `date +%F`). Change nothing else. Save to `runtime_data/tmp/issue-N.md`, then `gh issue edit N --body-file runtime_data/tmp/issue-N.md`.
4. Read `**Epic:** #E · **Feature:** #F` from the body. For each of `F` and `E` that still has `status: planned`, swap it for `status: in-progress`.
5. Run `ccaa-progress-sync` on `F`, then on `E`.
6. Reply in two lines: the story title and "started", then the next command: `/brainstorming Story #N ...` from `Docs/Project_Management/Issues/Milestone_02.md`.
