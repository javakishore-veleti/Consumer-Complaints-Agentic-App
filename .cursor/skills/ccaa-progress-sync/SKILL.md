---
name: ccaa-progress-sync
description: Rebuilds the checklist and Progress line of a CCAA (Consumer Complaints Agentic App) feature or epic GitHub issue from the real state of its child issues. Use when a ccaa- skill says to run ccaa-progress-sync, or when a feature or epic checklist looks stale.
---

# ccaa-progress-sync

Input: feature or epic issue number `P`. Run `gh` from the repository root: it reads the repository from the git remote, so never type the owner or repository name (D35). Scratch files go in `runtime_data/tmp/`.

1. `gh issue view P --json body,labels`. Find the checklist lines `- [ ] #C Title (state)` under `Stories:` or `Features:`. If there are none, stop.
2. For each child `C`: `gh issue view C --json state,labels,body`.
   - Drop the line if the child's `**Epic:**` or `**Feature:**` line does not point to `P` (it belongs elsewhere, for example an M03 story).
   - Closed: `- [x] #C Title (done)`.
   - Open with `status: in-progress`: `- [ ] #C Title (in-progress)`.
   - Otherwise: `- [ ] #C Title (planned)`.
   Keep the title text from the existing line.
3. Replace the `**Progress:**` line with `**Progress:** D of T done — <state>`. D counts done children, T counts the kept children. State is `done` when D equals T, `in-progress` when D is above 0 or any child is in progress, otherwise `planned`.
4. Save the body to `runtime_data/tmp/issue-P.md` and run `gh issue edit P --body-file runtime_data/tmp/issue-P.md`.
5. Set the label `status: planned` or `status: in-progress` to match the state. Never set `status: done` here: only `ccaa-feature-complete` and `ccaa-epic-complete` do that.
6. Report one line: `#P: D of T done`.
