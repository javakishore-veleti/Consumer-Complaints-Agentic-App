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


def test_compose_mounts_localhost_cfpb_imports_path():
    """M10-0005 / #212: host CCA imports dir bind-mounted for LOCAL_DATA_PATH_CFPB."""
    text = COMPOSE.read_text(encoding="utf-8")
    marker = "runtime_data/apps/datasets/CCA/complains_datasets/imports"
    assert marker in text
    # Same host path on both sides of the bind (workers see LOCAL_DATA_PATH_CFPB).
    assert any(marker in line and line.lstrip().startswith("-") and ":" in line for line in text.splitlines())


def test_compose_creates_dags_unpaused_by_default():
    """M10-0014 / #221: local DX — Admin can start workflows without a manual unpause."""
    text = COMPOSE.read_text(encoding="utf-8")
    assert "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION" in text
    assert any(
        "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION" in line and "false" in line.lower()
        for line in text.splitlines()
    )
    cfg = (REPO_ROOT / "CICD" / "Local" / "airflow" / "config" / "airflow.cfg").read_text(
        encoding="utf-8"
    )
    assert "dags_are_paused_at_creation = False" in cfg
