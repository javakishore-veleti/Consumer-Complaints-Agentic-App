"""M55-0001: spark-submit must use absolute path under bash -lc."""

from tests.conftest import REPO_ROOT

SPARK = REPO_ROOT / "Middleware" / "Airflow-dags" / "ccaa" / "lakehouse_spark.py"


def test_lakehouse_spark_uses_absolute_spark_binaries():
    text = SPARK.read_text(encoding="utf-8")
    assert 'SPARK_SUBMIT = "/opt/spark/bin/spark-submit"' in text
    assert 'SPARK_SQL = "/opt/spark/bin/spark-sql"' in text
    assert "{SPARK_SUBMIT}" in text
    assert 'f"spark-submit ' not in text
    assert '["spark-sql"' not in text
