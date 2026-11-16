"""D92: index_cfpb_pgvector DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "index_cfpb_pgvector.py"


def test_index_cfpb_pgvector_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="index_cfpb_pgvector"' in text or "dag_id='index_cfpb_pgvector'" in text
    assert "notify_finished" in text
    assert "ALL_DONE" in text or "all_done" in text
    assert "BACKEND_PGVECTOR" in text or "pgvector" in text
    assert "CCA_PGVECTOR_URL" in text or "resolve_pgvector_url" in text
    assert "from app." not in text
