"""M51-0003..0005: lakehouse hydrate DAGs + alembic seeds."""

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
VERS = REPO_ROOT / "Middleware" / "ConsumerComplaintsHandsOn" / "alembic" / "versions"


def test_taxonomy_curated_chroma_dags_exist():
    for name in (
        "hydrate_taxonomy_mode2_3m.py",
        "hydrate_curated_iceberg_3m.py",
        "hydrate_chroma_signatures_3m.py",
    ):
        text = (DAGS / name).read_text(encoding="utf-8")
        assert f'dag_id="{name[:-3]}"' in text
        assert "report_execution_status" in text
        assert "notify_execution_finished" in text


def test_alembic_0028_0030_seed_workflows():
    for rev, wf in (
        ("0028_seed_hydrate_taxonomy_mode2_3m_workflow.py", "hydrate_taxonomy_mode2_3m"),
        ("0029_seed_hydrate_curated_iceberg_3m_workflow.py", "hydrate_curated_iceberg_3m"),
        ("0030_seed_hydrate_chroma_signatures_3m_workflow.py", "hydrate_chroma_signatures_3m"),
    ):
        text = (VERS / rev).read_text(encoding="utf-8")
        assert f'workflow_name="{wf}"' in text
