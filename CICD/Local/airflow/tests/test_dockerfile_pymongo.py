"""Guard: local Airflow Dockerfile must install pymongo (M17-0009 / #257)."""

from pathlib import Path

AIRFLOW_DIR = Path(__file__).resolve().parents[1]
DOCKERFILE = AIRFLOW_DIR / "Dockerfile"
COMPOSE = AIRFLOW_DIR / "docker-compose.yaml"


def test_dockerfile_installs_pymongo() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "FROM apache/airflow:3.4.0" in text
    assert "pymongo" in text


def test_compose_builds_dockerfile() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "dockerfile: Dockerfile" in text
    assert "cca-airflow:3.4.0-pymongo" in text
    assert "image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.4.0}" not in text
