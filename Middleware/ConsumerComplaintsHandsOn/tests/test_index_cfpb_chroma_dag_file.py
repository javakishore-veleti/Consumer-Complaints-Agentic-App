"""D94: index_cfpb_chroma DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "index_cfpb_chroma.py"


def test_index_cfpb_chroma_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="index_cfpb_chroma"' in text or "dag_id='index_cfpb_chroma'" in text
    assert "notify_finished" in text
    assert "ALL_DONE" in text or "all_done" in text
    assert "BACKEND_CHROMA" in text or "chroma" in text
    assert "CCA_CHROMA_URL" in text or "resolve_chroma_url" in text
    assert "from app." not in text
