---
name: ccaa-milestone-log
description: Logs workflow progress of a CCAA (Consumer Complaints Agentic App) issue in the milestone file - marks the step in progress as Done with today's date and starts the next step. Use when a ccaa- skill says to run ccaa-milestone-log, after each Superpowers workflow step of a Milestone_02 story finishes, or when the user runs /ccaa-milestone-log N.
---

# ccaa-milestone-log

Input: issue number `N` (story, feature or epic) and optionally `begin`.

File: `docs/Project_Management/Issues/Milestone_02.md`, section 3. Every command has a row: `Issue | Step | Command | Status | Started | Completed`. Status is `Planned`, `In progress` or `Done`; dates are `YYYY-MM-DD` or `-`.

1. Find the rows of `N`: first cell is `#N`, `#N (...)`, `Feature #N` or `Epic #N`. They are in step order. If there are none, stop and say so (the issue is not in the table: add it first).
2. Today: `date +%F`.
3. `begin`: set the first row to `In progress` with Started today. Do nothing else.
4. No argument: take the row that is `In progress`.
   - If none is, but the first row is `Planned` (a feature or epic never begun), set it to `In progress` with Started today first.
   - Set that row to `Done` with Completed today. If its Started is `-`, set it to today as well.
   - Set the next row of `N`, if any, to `In progress` with Started today.
5. Change only the Status, Started and Completed cells. Leave Command and Step exactly as they are.
6. Refresh the `**Status:**` counts at the top. A story is an issue whose last row is a `/ccaa-story-complete`. "stories are left to build" is the number of those whose last row is not `Done`. "stories ... are already done" is 3 (the Phase 0 stories) plus the number whose last row is `Done`.
7. Do not commit. The change goes out with the next `ccaa-commit-push`, which includes this file when it is modified.

Steps that repeat: the pair "subagent-driven-development" and "`/ccaa-commit-push` after every task" is logged once, after the commit of the final task.
