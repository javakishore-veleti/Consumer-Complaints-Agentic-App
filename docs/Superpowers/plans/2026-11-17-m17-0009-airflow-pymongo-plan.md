# M17-0009 — Airflow pymongo plan

1. Add `CICD/Local/airflow/Dockerfile` installing `pymongo`.
2. Point `docker-compose.yaml` at `build:` + tagged image `cca-airflow:3.4.0-pymongo`.
3. `docker-all-up.sh` uses `--build` when a service Dockerfile exists.
4. Runbook troubleshooting row for the ModuleNotFoundError.
5. Smoke: `docker compose build` and `python -c 'import pymongo'` in the image.
