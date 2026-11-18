"""D44 / D67 / D70: filter_cfpb_3_months DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "filter_cfpb_3_months.py"


def test_filter_cfpb_3_months_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="filter_cfpb_3_months"' in text or "dag_id='filter_cfpb_3_months'" in text
    assert "resolve_and_filter" in text
    assert "notify_finished" in text
    assert "ALL_DONE" in text or "all_done" in text
    assert "report_execution_status" in text or "status_callback" in text
    assert "filter_by_date" in text or "filter_path_by_date_received" in text
    assert "list_filter_inputs" in text
    assert "prepare_run_folder" in text
    assert "report_import_run_create" in text
    assert "report_import_run_update" in text
    assert "dataset_dir" in text
    assert "from app." not in text
