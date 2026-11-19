# M45-0002 / #321 — Implementation plan

1. Add `hydrate_raw_headers.py` pure helpers + shell verify (TDD).
2. Add `hydrate_raw_3m.py` PySpark job.
3. Add `stage_unzip_3m.sh` + `run_hydrate_raw_3m.sh`.
4. Add npm `local:iceberg:hydrate-raw-3m`; document in Iceberg README.
5. Run hydrate against local Lift 3m (~1.97M); confirm COUNT > 0 and schema.
6. Commit-push; PR/merge; story-complete. Count reconcile proof = #323.
