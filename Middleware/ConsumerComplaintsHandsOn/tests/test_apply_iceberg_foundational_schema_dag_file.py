"""M58-0001 / #400: apply_iceberg_foundational_schema DAG under Middleware/Airflow-dags."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "apply_iceberg_foundational_schema.py"
SCRIPT = (
    REPO_ROOT
    / "CICD"
    / "Local"
    / "iceberg"
    / "scripts"
    / "apply_iceberg_foundational_ddl_incontainer.sh"
)


def test_apply_iceberg_foundational_schema_dag_file_exists_with_tasks():
    text = DAG.read_text()
    assert 'dag_id="apply_iceberg_foundational_schema"' in text
    assert "apply_foundational_ddl" in text
    assert "notify_finished" in text


def test_foundational_ddl_script_orders_all_zones():
    text = SCRIPT.read_text()
    assert "create_raw_tables.sql" in text
    assert "create_refined_tables.sql" in text
    assert "create_taxonomy_tables.sql" in text
    assert "create_curated_tables.sql" in text
    assert text.index("create_raw_tables.sql") < text.index("create_refined_tables.sql")
    assert text.index("create_refined_tables.sql") < text.index("create_taxonomy_tables.sql")
    assert text.index("create_taxonomy_tables.sql") < text.index("create_curated_tables.sql")


def test_alembic_0033_seeds_foundational_workflow():
    mig = (
        REPO_ROOT
        / "Middleware"
        / "ConsumerComplaintsHandsOn"
        / "alembic"
        / "versions"
        / "0033_seed_apply_iceberg_foundational_schema.py"
    )
    text = mig.read_text()
    assert 'workflow_name="apply_iceberg_foundational_schema"' in text
    assert 'engine_workflow_id="apply_iceberg_foundational_schema"' in text
