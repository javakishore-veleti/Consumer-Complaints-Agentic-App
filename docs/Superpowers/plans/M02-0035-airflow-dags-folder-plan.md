# M02-0035 (#85) Airflow DAGs folder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put Airflow DAGs in `Middleware/Airflow-dags`, mount that folder by relative path in the local Airflow 3.4.0 compose file, set a short local DAG-folder refresh, remove the repository-root `dags/`, and update docs so nothing still points at the old path.

**Architecture:** D44 already places DAGs outside the FastAPI app root. This plan only moves the empty folder, rewires the compose volume, and sets `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL=10` (D62). No production DAG code. CI asserts paths and compose text; a live "new DAG without restart" check is manual when Airflow is running.

**Tech Stack:** Docker Compose, Apache Airflow 3.4.0, pytest, `uv`.

Spec: `docs/Superpowers/specs/M02-0035-airflow-dags-folder-design.md`. Decisions: D44, D54, D62 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- Paths are relative to the **repository root** unless a step says otherwise. App tests run from `Middleware/ConsumerComplaintsHandsOn` with `uv run pytest`.
- Mount string exactly: `../../../Middleware/Airflow-dags:/opt/airflow/dags` (from `CICD/Local/airflow/`).
- Refresh env exactly: `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL: '10'` under `x-airflow-common` → `environment`. Do **not** set `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL` (deprecated in Airflow 3).
- Keep the empty folder with `.gitkeep` only (no README inside `Airflow-dags` for MVP, D54).
- Delete repository-root `dags/` entirely (including `.gitkeep`).
- No live Airflow in CI. Manual refresh check is documented only.
- Scratch / throwaway probe DAGs go under `Middleware/Airflow-dags/` and must be deleted after the manual check; never commit a probe DAG.
- Commit with `/ccaa-commit-push 85` (never a raw `git commit`).

## File Structure

| File | Responsibility |
|---|---|
| `Middleware/Airflow-dags/.gitkeep` (create) | Keeps the empty DAGs folder in git |
| `dags/.gitkeep` (delete) / `dags/` (remove) | Old location gone |
| `CICD/Local/airflow/docker-compose.yaml` (modify) | Relative mount + `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL` + comments |
| `Middleware/ConsumerComplaintsHandsOn/tests/test_airflow_dags_folder.py` (create) | Asserts folder layout and compose text |
| `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` (modify) | Present-tense `Airflow-dags`; no root `dags/` |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (modify) | D44 marked built by #85 (D62 already recorded with the spec) |
| Root / Middleware READMEs | Touch only if they still mention root `dags/` (today they do not) |

---

### Task 1: Folder, compose mount, refresh env, and path test

**Files:**
- Create: `Middleware/Airflow-dags/.gitkeep`
- Delete: `dags/.gitkeep` (and the empty `dags/` directory)
- Modify: `CICD/Local/airflow/docker-compose.yaml`
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_airflow_dags_folder.py` (create)

**Interfaces:**
- Consumes: `REPO_ROOT` from `tests/conftest.py` (`PROJECT_ROOT.parents[1]`).
- Produces: empty `Middleware/Airflow-dags/`; compose mounts that path and sets refresh to 10 seconds.

- [ ] **Step 1: Write the failing test**

Create `Middleware/ConsumerComplaintsHandsOn/tests/test_airflow_dags_folder.py`:

```python
"""D44 / D62: DAGs live in Middleware/Airflow-dags; local Airflow mounts it and refreshes every 10s."""

from pathlib import Path

from tests.conftest import REPO_ROOT

COMPOSE = REPO_ROOT / "CICD" / "Local" / "airflow" / "docker-compose.yaml"
AIRFLOW_DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
OLD_DAGS = REPO_ROOT / "dags"


def test_middleware_airflow_dags_exists_and_root_dags_is_gone():
    assert AIRFLOW_DAGS.is_dir()
    assert not OLD_DAGS.exists()


def test_compose_mounts_middleware_airflow_dags_by_relative_path():
    text = COMPOSE.read_text()
    assert "../../../Middleware/Airflow-dags:/opt/airflow/dags" in text
    assert "../../../dags:" not in text


def test_compose_sets_short_local_dag_processor_refresh_interval():
    text = COMPOSE.read_text()
    assert "AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL" in text
    assert "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL" not in text
    # Accept quoted or bare 10 on the same logical assignment line.
    assert any(
        line.strip().replace(" ", "").startswith("AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL:")
        and "10" in line
        for line in text.splitlines()
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run from `Middleware/ConsumerComplaintsHandsOn`:

```bash
uv run pytest tests/test_airflow_dags_folder.py -v
```

Expected: FAIL — `Middleware/Airflow-dags` missing and/or compose still mounts `../../../dags`.

- [ ] **Step 3: Create the folder and remove the old one**

```bash
mkdir -p Middleware/Airflow-dags
touch Middleware/Airflow-dags/.gitkeep
rm -f dags/.gitkeep
rmdir dags
```

(Run from the repository root. If `rmdir dags` fails because the directory is not empty, stop and inspect — nothing but `.gitkeep` should be there.)

- [ ] **Step 4: Update compose**

In `CICD/Local/airflow/docker-compose.yaml`:

1. Change the header comment line about DAGs from `<repo>/dags` to `<repo>/Middleware/Airflow-dags`. Add one short comment that local refresh is 10s via `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL` (Airflow 3.4.0; local-only; default is 300).
2. Under `x-airflow-common` → `environment` (`&airflow-common-env`), add:

```yaml
    # Local only: discover new DAG files quickly (Airflow 3.4.0; default 300). Do not copy to cloud stacks.
    AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL: '10'
```

3. Change the volume from:

```yaml
    - ../../../dags:/opt/airflow/dags
```

to:

```yaml
    - ../../../Middleware/Airflow-dags:/opt/airflow/dags
```

Leave `./logs`, `./config`, and `./plugins` mounts unchanged.

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_airflow_dags_folder.py -v
```

Expected: PASS (all three tests).

- [ ] **Step 6: Commit**

```bash
/ccaa-commit-push 85
```

Message theme (the skill writes the exact subject): move DAGs to `Middleware/Airflow-dags`, mount by relative path, short local refresh.

---

### Task 2: Docs, DESIGN D44 built, self-review

**Files:**
- Modify: `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md`
- Modify: `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (D44 status only; D62 already present)
- Check: root `README.md`, `Middleware/README.md` (edit only if they mention root `dags/`)

**Interfaces:**
- Consumes: Task 1 layout and compose.
- Produces: docs that match D44 built + D62; no mention of repository-root `dags/` as the live location.

- [ ] **Step 1: Update ARCHITECTURE.md**

In the tree under section 3, change the `Middleware/Airflow-dags/` line from planned / "replaces dags/" to present tense, for example:

```text
Middleware/Airflow-dags/      Airflow DAGs, outside the FastAPI app root, mounted into Airflow by relative path (D44, D62)
```

Do not mention repository-root `dags/` anywhere in this file after the edit.

- [ ] **Step 2: Mark D44 built in DESIGN.md**

In the D44 decision row, replace `**Not built yet.**` with:

```text
**Built in story #85** (spec `docs/Superpowers/specs/M02-0035-airflow-dags-folder-design.md`; local refresh D62).
```

Leave the D44 **Why** column as is. Confirm D62 is already the next row after D61; do not renumber.

- [ ] **Step 3: README scan**

```bash
rg -n '\bdags\b|Airflow-dags' README.md Middleware/README.md Middleware/ConsumerComplaintsHandsOn/README.md || true
```

If any file still presents repository-root `dags/` as the DAG location, fix that sentence. If there is no mention, leave the READMEs unchanged.

- [ ] **Step 4: Full app test suite (sanity)**

From `Middleware/ConsumerComplaintsHandsOn`:

```bash
uv run pytest -q
```

Expected: PASS (including `test_airflow_dags_folder.py`).

- [ ] **Step 5: Manual refresh check (optional if Airflow is already up; skip in CI)**

Only when local Airflow containers are running:

```bash
cd CICD/Local/airflow
# write a throwaway DAG under ../../../Middleware/Airflow-dags/probe_m02_0035.py
# wait >= 20s — do NOT restart containers
docker compose --profile debug run --rm airflow-cli dags list | grep probe_m02_0035
rm -f ../../../Middleware/Airflow-dags/probe_m02_0035.py
```

Throwaway DAG body (do not commit):

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

with DAG(dag_id="probe_m02_0035", start_date=datetime(2024, 1, 1), schedule=None, catchup=False):
    EmptyOperator(task_id="noop")
```

- [ ] **Step 6: Self-review against the spec**

Confirm each acceptance bullet has evidence:

| Acceptance | Evidence |
|---|---|
| `Middleware/Airflow-dags` exists; root `dags/` gone | Task 1 test + filesystem |
| Compose mounts by relative path | Task 1 test + compose volume line |
| New DAG appears without restart | Manual Step 5 (or documented; CI does not require it) |
| Short refresh for local use (Airflow 3.4.0 name) | `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL: '10'` |
| ARCHITECTURE / READMEs no longer mention old folder | Steps 1 and 3 |

- [ ] **Step 7: Commit**

```bash
/ccaa-commit-push 85
```

---

## Plan self-review

1. **Spec coverage:** Folder + remove root `dags/` (Task 1); relative mount (Task 1); refresh env D62 (Task 1); CI assertions without live Airflow (Task 1); manual no-restart check (Task 2); ARCHITECTURE / DESIGN / README (Task 2). Out of scope left out: real DAGs, cloud compose, custom image.
2. **Placeholders:** None; mount string, env name/value, test code, and probe DAG are concrete.
3. **Consistency:** Mount path and `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL` / `10` match the spec and D62; deprecated scheduler env var is explicitly forbidden in the test.
