"""Guard: local Mongo first-boot init creates complaints collection (M17-0010 / #259)."""

from pathlib import Path

MONGO_DIR = Path(__file__).resolve().parents[1]
INIT_JS = MONGO_DIR / "docker-entrypoint-initdb.d" / "01-init-complaints.js"
COMPOSE = MONGO_DIR / "docker-compose.yaml"


def test_init_script_creates_complaints_collection() -> None:
    text = INIT_JS.read_text(encoding="utf-8")
    assert "consumer_comp_db" in text
    assert "complaints" in text
    assert "Complaint ID" in text
    assert "unique" in text


def test_compose_mounts_initdb() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "docker-entrypoint-initdb.d" in text
    assert "MONGO_INITDB_DATABASE: consumer_comp_db" in text
    assert "authSource=admin" in text
