# M10-0016 (#223) Runbook 3m: download is filter prerequisite

## Decision
1. Keep `download_cfpb_all` in the 3m path because `filter_cfpb_3_months` needs `complaints.csv.zip` on disk.
2. Rewrite §1 so operators see it as a **prerequisite**, not the runbook goal.
3. UI path: **DataSets → Imports** accordion rows (no MIO left-nav).
