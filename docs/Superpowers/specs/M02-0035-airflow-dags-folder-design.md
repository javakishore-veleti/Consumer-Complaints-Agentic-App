# M02-0035 (#85) Move the DAGs to Middleware/Airflow-dags

Decisions: D44 and D62 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. D44 already places the DAGs outside the FastAPI app root and mounts them by relative path; this story builds that. D62 pins the Airflow 3.4.0 local refresh setting (decided without the user present; review and reverse if needed).

## Goal

`Middleware/Airflow-dags` is the only DAGs folder. Local Airflow mounts it by relative path from `CICD/Local/airflow/docker-compose.yaml`, so a new or edited DAG file shows up without stopping or recreating the container. The repository-root `dags/` is removed. Docs no longer mention the old folder.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Keep root `dags/` and symlink into Middleware | Two paths to remember; breaks on Windows; rejects D44 |
| B (chosen) | `Middleware/Airflow-dags` only; compose mounts `../../../Middleware/Airflow-dags:/opt/airflow/dags` | Matches D44; one place for later DAG stories (#59, #61, …) |
| C | Bake DAGs into a custom Airflow image | Every DAG edit needs a rebuild; rejects "appears without restart" |

## Layout

| Path | Role |
|---|---|
| `Middleware/Airflow-dags/` | Host folder for DAG Python files (empty for now; later stories add DAGs) |
| `Middleware/Airflow-dags/.gitkeep` | Keeps the empty folder in git (same pattern as `CICD/Local/airflow/plugins/.gitkeep`) |
| `dags/` (repo root) | **Removed** entirely; no leftover `.gitkeep` |
| `CICD/Local/airflow/docker-compose.yaml` | Volume mount + short local refresh env (D62) |

No README inside `Airflow-dags` for MVP (D54): `.gitkeep` is enough. Real DAG modules come in later stories under feature #56.

## Compose mount and refresh (D44, D62)

From `CICD/Local/airflow/` the relative mount is:

```yaml
volumes:
  - ../../../Middleware/Airflow-dags:/opt/airflow/dags
```

Header comment becomes: DAGs live in `<repo>/Middleware/Airflow-dags` (not `<repo>/dags`).

**Airflow 3.4.0 refresh:** `scheduler.dag_dir_list_interval` is **deprecated since 3.0** and moved to `dag_processor.refresh_interval`. Local compose sets (on `x-airflow-common` environment, so scheduler, dag-processor, and the rest share it):

```yaml
AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL: '10'
```

- Default is `300` (5 minutes). `10` is local-only so a laptop sees a new file within about one refresh cycle.
- Document in the compose comment that this is for local use only; production/cloud stacks keep the default (or their own value).
- Do **not** set the deprecated `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL`.
- `min_file_process_interval` stays at the image default (edits of already-known files); acceptance is about a **new** file appearing.

## Verification

**CI / unit (no live Airflow):** `tests/test_airflow_dags_folder.py` under the FastAPI app (uses `REPO_ROOT` from `conftest.py`):

1. `Middleware/Airflow-dags` exists as a directory.
2. Repo-root `dags/` does not exist.
3. `CICD/Local/airflow/docker-compose.yaml` contains the mount `../../../Middleware/Airflow-dags:/opt/airflow/dags` and does not contain `../../../dags:`.
4. The same file contains `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL` with value `10` (quoted or unquoted).

**Manual (local, when Airflow is up — not CI):** documented in the compose header and the plan:

1. `cd CICD/Local/airflow && docker compose up -d` (if not already running).
2. Drop a throwaway DAG under `Middleware/Airflow-dags/` (e.g. `probe_m02_0035.py` with a trivial `DAG(dag_id="probe_m02_0035", ...)`).
3. Wait at least 10–20 seconds (one refresh interval plus parse).
4. `docker compose --profile debug run --rm airflow-cli dags list` (or `docker compose exec airflow-scheduler airflow dags list`) and confirm `probe_m02_0035` appears **without** `docker compose restart` / recreate.
5. Delete the throwaway file.

## Docs

| File | Change |
|---|---|
| `ARCHITECTURE.md` tree | `Middleware/Airflow-dags/` present tense (D44); drop "planned" and any "replaces dags/" wording |
| `DESIGN.md` D44 | "**Not built yet.**" → built by story #85; D62 added |
| Root `README.md`, `Middleware/README.md` | Confirm they do not mention repo-root `dags/`; no change required unless a stray mention appears |

## Out of scope

- Any real ingest/download DAG (later stories under #56).
- Custom Airflow image / `_PIP_ADDITIONAL_REQUIREMENTS` for DAG deps.
- Cloud or non-local Airflow compose.
- Changing `bundle_refresh_check_interval` or `min_file_process_interval`.
- A CI job that starts Airflow.
