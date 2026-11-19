"""M51-0002 / #342: hydrate_refined_iceberg_3m DAG file."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "hydrate_refined_iceberg_3m.py"


def test_hydrate_refined_dag_exists():
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="hydrate_refined_iceberg_3m"' in text
    assert "hydrate_refined_3m.py" in text
    assert "report_execution_status" in text
    assert "notify_execution_finished" in text
