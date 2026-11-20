"""M55-0009: curated Spark must fit ~8GiB Docker Desktop (not tip OOM killer)."""

from tests.conftest import REPO_ROOT

LAKEHOUSE = REPO_ROOT / "Middleware" / "Airflow-dags" / "ccaa" / "lakehouse_spark.py"
CURATED = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "hydrate_curated_3m.py"
SHELL = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "run_hydrate_curated_3m.sh"
README = REPO_ROOT / "CICD" / "Local" / "iceberg" / "README.md"


def test_default_driver_memory_is_2g_for_docker_headroom():
    text = LAKEHOUSE.read_text(encoding="utf-8")
    assert 'or "2g"' in text or "or '2g'" in text
    assert 'or "4g"' not in text


def test_spark_submit_passes_shuffle_and_aqe_confs():
    text = LAKEHOUSE.read_text(encoding="utf-8")
    assert "spark.sql.shuffle.partitions" in text
    assert "spark.sql.adaptive.enabled" in text
    assert "spark.driver.maxResultSize" in text


def test_curated_script_sets_spill_friendly_confs():
    text = CURATED.read_text(encoding="utf-8")
    assert "spark.sql.shuffle.partitions" in text
    assert "spark.sql.adaptive.enabled" in text


def test_curated_shell_defaults_to_2g():
    text = SHELL.read_text(encoding="utf-8")
    assert "2g" in text
    assert "CCA_SPARK_DRIVER_MEMORY" in text


def test_readme_documents_docker_memory_headroom():
    text = README.read_text(encoding="utf-8")
    assert "CCA_SPARK_DRIVER_MEMORY" in text
    assert "headroom" in text.lower() or "OOMKill" in text or "OOM" in text
    assert "2g" in text
