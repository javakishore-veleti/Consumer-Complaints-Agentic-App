"""M55-0006: Spark hydrate uses Middleware execution_id, not Airflow run_id paths."""

from tests.conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "run_hydrate_raw_3m_incontainer.sh"
DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "hydrate_raw_iceberg_3m.py"


def test_incontainer_script_sanitizes_run_id_for_stage_dir():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "STAGE_RUN_ID=" in text
    assert "tr ':/+'" in text
    assert 'stage_unzip_3m.sh" "$STAGE_RUN_ID"' in text
    assert '--run-id "$RUN_ID"' in text


def test_hydrate_raw_prefers_middleware_execution_id():
    text = DAG.read_text(encoding="utf-8")
    assert "run_id = _execution_id(context) or _engine_run_id(context)" in text
    assert "CCA_RAW_RUN_ID=" in text
    assert "out[-4000:]" in text
