# M55-0009 Curated OOM Docker headroom — plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement this plan task-by-task.

**Goal:** Fit curated Spark hydrate in ~8 GiB Docker Desktop without OOMKilled.

**Architecture:** Lower default `--driver-memory` to 2g; add spill-friendly Spark confs on `spark-submit` and in `hydrate_curated_3m.py`; document headroom.

**Tech stack:** Airflow `lakehouse_spark.py`, Iceberg scripts, pytest string contracts (existing M55 pattern).

### Task 1: Failing tests for 2g default + shuffle/AQE confs

**Files:**
- Create/modify: `Middleware/ConsumerComplaintsHandsOn/tests/test_m55_curated_oom_headroom.py`

**Steps:** Assert lakehouse_spark default `"2g"`, `--conf spark.sql.shuffle.partitions=8`, `adaptive.enabled`; curated script sets shuffle/AQE; shell uses `2g` default.

### Task 2: Implement lakehouse_spark + shell + curated confs + README

**Files:**
- Modify: `Middleware/Airflow-dags/ccaa/lakehouse_spark.py`
- Modify: `CICD/Local/iceberg/scripts/run_hydrate_curated_3m.sh`
- Modify: `CICD/Local/iceberg/scripts/hydrate_curated_3m.py`
- Modify: `CICD/Local/iceberg/README.md`

### Task 3: Verify + commit-push + PR

Run targeted pytest + `npm run local:api:lint` + `npm run local:api:test`; `/ccaa-commit-push 387`; open/merge PR.
