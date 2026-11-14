---
name: ccaa-milestone-log
description: Updates the Status, Started and Completed columns of an issue's row in the CCAA (Consumer Complaints Agentic App) milestone file, then commits and pushes. Use when a ccaa- skill says to run ccaa-milestone-log, or when the user runs /ccaa-milestone-log N started or completed.
---

# ccaa-milestone-log

Input: issue number `N` (story, feature or epic) and an event, `started` or `completed`.

File: `Docs/Project_Management/Issues/Milestone_02.md`, section 3, the phase tables with the columns `Issue | Status | Started | Completed | Commands, in order`.

1. Find the row whose first cell is `#N`, `#N (...)`, `Feature #N` or `Epic #N`. If there is none, stop and say so (the issue is not in the table: add it first).
2. Today: `date +%F`.
3. `started`: set Status to `In progress`, and Started to today unless it already holds a date.
4. `completed`: set Status to `Done` and Completed to today. If Started is `-`, set it to today as well.
5. Change only those three cells of that row. Leave the commands cell exactly as it is.
6. Refresh the count at the top: in the `**Status:**` line, set "stories are left to build" to the number of story rows in section 3 (first cell starts with `#`) whose Status is not `Done`.
7. Run `ccaa-commit-push` with the message `M02: log #N <event>`. This is a docs-only change, so lint and tests are skipped.
