"""M45-0003 / #322: hydrate_raw_iceberg_3m DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "hydrate_raw_iceberg_3m.py"


def test_hydrate_raw_iceberg_3m_dag_file_exists_with_tasks():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="hydrate_raw_iceberg_3m"' in text
    assert "sense_lift_3m" in text
    assert "pre_ingest_gate" in text
    assert "hydrate_raw" in text
    assert "dq_checks" in text
    assert "cleanup_stage" in text
    assert "cca-spark-iceberg" in text or "spark_container_name" in text
    assert "from app." not in text
    assert "download" not in text.lower() or "Does not re-download" in text
