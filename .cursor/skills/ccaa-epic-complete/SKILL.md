---
name: ccaa-epic-complete
description: Completes a CCAA (Consumer Complaints Agentic App) GitHub epic once all its features are done - marks it done, closes it and marks the milestone file complete. Use when the user runs /ccaa-epic-complete N.
disable-model-invocation: true
---

# ccaa-epic-complete

Input: epic issue number `N`. Run `gh` from the repository root: it reads the repository from the git remote, so never type the owner or repository name (D35). Scratch files go in `runtime_data/tmp/`.

1. Run `ccaa-progress-sync` on `N`.
2. If any feature in the checklist is not closed, stop and list it. Do not change the epic.
3. Body: replace or append the `**Status:** Done — All F features are done: #a, #b, #c.` line.
4. `gh issue edit N --remove-label "status: planned" --remove-label "status: in-progress" --add-label "status: done" --body-file runtime_data/tmp/issue-N.md`, then `gh issue close N --reason completed`.
5. Run `ccaa-milestone-log N`.
6. In `docs/Project_Management/Issues/Milestone_02.md`, change the `**Status:**` line to `**Status: complete.**` with the final epic, feature and story counts.
7. Run `ccaa-commit-push` with the message `M02: mark milestone complete`.
