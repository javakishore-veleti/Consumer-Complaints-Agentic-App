"""M55-0007: refined/taxonomy/curated hydrates createOrReplace; DAGs use execution_id."""

from tests.conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts"
DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"


def test_refined_curated_taxonomy_use_create_or_replace():
    for name in (
        "hydrate_refined_3m.py",
        "hydrate_curated_3m.py",
        "hydrate_taxonomy_mode2_3m.py",
    ):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "createOrReplace()" in text
        assert "DELETE FROM" not in text.replace("# (DELETE FROM", "")


def test_lakehouse_dags_prefer_middleware_execution_id():
    for name in (
        "hydrate_refined_iceberg_3m.py",
        "hydrate_taxonomy_mode2_3m.py",
        "hydrate_curated_iceberg_3m.py",
        "hydrate_chroma_signatures_3m.py",
    ):
        text = (DAGS / name).read_text(encoding="utf-8")
        assert "execution_id(context) or engine_run_id(context)" in text


def test_lakehouse_spark_docker_exec_includes_stdout_tail():
    text = (DAGS / "ccaa" / "lakehouse_spark.py").read_text(encoding="utf-8")
    assert "out[-4000:]" in text
