"""M55-0010: static driver configs must not be set via spark.conf after getOrCreate."""

from tests.conftest import REPO_ROOT

CURATED = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "hydrate_curated_3m.py"
LAKEHOUSE = REPO_ROOT / "Middleware" / "Airflow-dags" / "ccaa" / "lakehouse_spark.py"


def test_curated_script_does_not_set_max_result_size_at_runtime():
    text = CURATED.read_text(encoding="utf-8")
    assert 'spark.conf.set("spark.driver.maxResultSize"' not in text
    assert "spark.driver.maxResultSize" not in text


def test_max_result_size_still_passed_on_spark_submit():
    text = LAKEHOUSE.read_text(encoding="utf-8")
    assert "spark.driver.maxResultSize" in text
