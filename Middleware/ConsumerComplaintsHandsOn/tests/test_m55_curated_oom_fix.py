"""M55-0008: curated hydrate must avoid Python UDFs and request enough driver memory."""

from tests.conftest import REPO_ROOT

CURATED = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "hydrate_curated_3m.py"
LAKEHOUSE = REPO_ROOT / "Middleware" / "Airflow-dags" / "ccaa" / "lakehouse_spark.py"
SHELL = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "run_hydrate_curated_3m.sh"


def test_curated_avoids_python_udfs_and_broadcasts_signatures():
    text = CURATED.read_text(encoding="utf-8")
    assert "@F.udf" not in text
    assert "udf_parent" not in text
    assert "broadcast(" in text
    assert "organization_aliases" in text
    # Prefer write then single count (avoid pre-write full materialization).
    write_idx = text.index("writeTo")
    assert ".count()" in text[write_idx:]
    assert text[:write_idx].count(".count()") <= 1  # aliases seed count only


def test_spark_submit_sets_driver_memory():
    text = LAKEHOUSE.read_text(encoding="utf-8")
    assert "--driver-memory" in text
    assert "CCA_SPARK_DRIVER_MEMORY" in text or "4g" in text


def test_curated_shell_sets_driver_memory():
    text = SHELL.read_text(encoding="utf-8")
    assert "--driver-memory" in text
