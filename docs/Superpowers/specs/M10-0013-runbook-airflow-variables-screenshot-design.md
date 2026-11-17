# M10-0013 (#220) Runbook Airflow Variables check + screenshot

## Decision
1. Runbook §0.4 points operators to http://127.0.0.1:8080/variables after Sync secrets.
2. Commit a redacted screenshot at `docs/Runbooks/Localhost/assets/airflow-variables-after-sync.png` (no personal `/Users/<name>` path — use `$HOME/…`).
3. Remind that worker-facing Chroma/Redis URLs must use `host.docker.internal`.
