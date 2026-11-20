"""M55-0004: Iceberg hydrate shell/DAG helpers must use absolute spark binaries."""

from tests.conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts"
RAW_DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "hydrate_raw_iceberg_3m.py"


def test_incontainer_raw_hydrate_uses_absolute_spark_submit():
    text = (SCRIPTS / "run_hydrate_raw_3m_incontainer.sh").read_text(encoding="utf-8")
    assert "/opt/spark/bin/spark-submit" in text
    assert "\nspark-submit " not in text
    assert not text.strip().startswith("spark-submit ")


def test_hydrate_shell_wrappers_use_absolute_spark_submit():
    for name in (
        "run_hydrate_raw_3m.sh",
        "run_hydrate_refined_3m.sh",
        "run_hydrate_taxonomy_mode2_3m.sh",
        "run_hydrate_curated_3m.sh",
        "run_hydrate_chroma_signatures_3m.sh",
    ):
        path = SCRIPTS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # docker exec / bash invocations must not use bare spark-submit as a command token
        assert "spark-submit" not in text.replace("/opt/spark/bin/spark-submit", "")


def test_hydrate_raw_dag_dq_uses_absolute_spark_sql():
    text = RAW_DAG.read_text(encoding="utf-8")
    assert '["/opt/spark/bin/spark-sql"' in text
    assert '["spark-sql"' not in text
