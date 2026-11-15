"""D44 / D63: download_cfpb_all DAG file is present under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "download_cfpb_all.py"


def test_download_cfpb_all_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="download_cfpb_all"' in text or "dag_id='download_cfpb_all'" in text
    assert "TODO story #59" in text
    assert "from app." not in text
