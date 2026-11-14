---
name: ccaa-feature-complete
description: Completes a CCAA (Consumer Complaints Agentic App) GitHub feature once all its stories are done - marks it done, closes it and refreshes the epic. Use when the user runs /ccaa-feature-complete N.
disable-model-invocation: true
---

# ccaa-feature-complete

Input: feature issue number `N`. Repo: `javakishore-veleti/Consumer-Complaints-Agentic-App` (pass `--repo` to every `gh` call). Scratch files go in `runtime_data/tmp/`.

1. Run `ccaa-progress-sync` on `N`.
2. Read the checklist. If any story is not closed, stop and list the open ones with their numbers. Do not change the feature.
3. Body: replace or append the `**Status:**` line with `**Status:** Done — All T stories are done: #a, #b, #c.` (T is the story count).
4. `gh issue edit N --remove-label "status: planned" --remove-label "status: in-progress" --add-label "status: done" --body-file runtime_data/tmp/issue-N.md`, then `gh issue close N --reason completed`.
5. Read `**Epic:** #E` and run `ccaa-progress-sync` on `E`. If every feature of `E` is done, end with: "All features of #E are done. Run `/ccaa-epic-complete E`."
