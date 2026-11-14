---
name: ccaa-story-complete
description: Completes a CCAA (Consumer Complaints Agentic App) GitHub story - verifies acceptance, ticks it, records commits, labels it done, closes it and refreshes the feature. Use when the user runs /ccaa-story-complete N after the story is built, reviewed and pushed.
disable-model-invocation: true
---

# ccaa-story-complete

Input: story issue number `N`. Run `gh` from the repository root: it reads the repository from the git remote, so never type the owner or repository name (D35). Scratch files go in `runtime_data/tmp/`.

1. `gh issue view N --json title,body,labels`. List every `- [ ]` acceptance item.
2. Verify each item with evidence (a test, a command, a file). For code stories run `npm run local:api:lint` and `npm run local:api:test` from the repo root. If any item is not proven, stop and list it. Do not tick it.
3. Work from the main checkout, not a story worktree. For a code story the story branch must already be merged into `main` (`/finishing-a-development-branch`, option 1, or a merged pull request) and `main` pushed. If not, stop and say so. If `git status -s` shows changes or `git status -sb` shows the branch ahead, run `ccaa-commit-push N` first.
4. Commits for this story: `git log --format=%h --grep="#N:"`.
5. Body: change every `- [ ]` to `- [x]`. Replace the `**Status:**` line with `**Status:** Done — <one sentence on what was built> (commits `a1b2c3d`, `e4f5a6b`; D## if a decision was recorded).`
6. `gh issue edit N --remove-label "status: planned" --remove-label "status: in-progress" --add-label "status: done" --body-file runtime_data/tmp/issue-N.md`, then `gh issue close N --reason completed`. Ignore "label not found" on a label the issue never had.
7. Run `ccaa-milestone-log N` (this command's row is `In progress`, so it becomes `Done`), then `ccaa-commit-push N` with the summary `complete story`.
8. Read `**Feature:** #F` and run `ccaa-progress-sync` on `F`. If every story of `F` is now done, end with: "All stories of #F are done. Run `/ccaa-feature-complete F`." Otherwise name the next story from `docs/Project_Management/Issues/Milestone_02.md`.
9. Do not close the feature or the epic here.
