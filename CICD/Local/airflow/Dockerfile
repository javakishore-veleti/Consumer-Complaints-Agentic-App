# Local Airflow image with DAG deps (M17-0009 / #257).
# Mongo ingest DAGs need pymongo (DESIGN D51). Prefer bake-in over _PIP_ADDITIONAL_REQUIREMENTS.
FROM apache/airflow:3.4.0

USER airflow
RUN pip install --no-cache-dir "pymongo>=4.6,<5"
