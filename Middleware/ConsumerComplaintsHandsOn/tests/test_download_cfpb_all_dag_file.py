"""D44 / D63 / D67: download_cfpb_all DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "download_cfpb_all.py"


def test_download_cfpb_all_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="download_cfpb_all"' in text or "dag_id='download_cfpb_all'" in text
    assert "notify_finished" in text
    assert "ALL_DONE" in text or "all_done" in text
    assert "report_execution_status" in text or "status_callback" in text
    assert "TODO story #59" not in text
    assert "from app." not in text
    assert "split_parts" in text or "stage_parts" in text
    assert "CCA_CFPB_SPLIT_SOURCE_PATH" in text or "stage_from_env" in text
