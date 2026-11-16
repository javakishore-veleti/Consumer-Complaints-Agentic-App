"""D88 / D67: index_cfpb_all DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "index_cfpb_all.py"


def test_index_cfpb_all_dag_file_exists_with_dag_id():
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="index_cfpb_all"' in text or "dag_id='index_cfpb_all'" in text
    assert "resolve_and_index" in text
    assert "notify_finished" in text
    assert "CCA_VECTOR_STORE_PATH" in text or "resolve_vector_store_path" in text
