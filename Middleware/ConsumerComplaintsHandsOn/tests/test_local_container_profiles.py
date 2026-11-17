"""Lite local Docker profiles (D78 / story #120)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL = REPO_ROOT / "CICD" / "Local"
PROFILES_MAP = LOCAL / "profiles.map"
DOCKER_PROFILES_SH = LOCAL / "docker-profiles.sh"
STATUS_SH = LOCAL / "docker-all-status.sh"
PACKAGE_JSON = REPO_ROOT / "package.json"

EXPECTED = {
    "sqlite": ["airflow"],
    "postgres": ["airflow", "postgres"],
    "mongodb": ["airflow", "mongodb"],
    "pgvector": ["airflow", "postgres"],
    "chroma": ["airflow", "chroma"],
    "redis": ["airflow", "redis"],
}


def _parse_profiles_map() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for raw in PROFILES_MAP.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.split()
    return out


def test_profiles_map_defines_sqlite_postgres_mongodb() -> None:
    assert PROFILES_MAP.is_file()
    parsed = _parse_profiles_map()
    assert parsed == EXPECTED


def test_cca_profile_services_matches_map() -> None:
    assert DOCKER_PROFILES_SH.is_file()
    script = f"""
set -euo pipefail
source "{DOCKER_PROFILES_SH}"
for p in sqlite postgres mongodb pgvector chroma redis; do
  echo "BEGIN:$p"
  cca_profile_services "$p"
  echo "END:$p"
done
"""
    result = subprocess.run(
        ["bash", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    got: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("BEGIN:"):
            current = line.split(":", 1)[1]
            buf = []
        elif line.startswith("END:"):
            assert current == line.split(":", 1)[1]
            got[current] = buf
            current = None
        elif current is not None and line.strip():
            buf.append(line.strip())
    assert got == EXPECTED


@pytest.mark.parametrize("profile", ["sqlite", "postgres", "mongodb", "pgvector", "chroma", "redis"])
def test_status_script_prints_expected_for_profile(profile: str) -> None:
    result = subprocess.run(
        ["bash", str(STATUS_SH), "--profile", profile],
        check=True,
        capture_output=True,
        text=True,
    )
    assert f"profile={profile}" in result.stdout
    expected = " ".join(EXPECTED[profile])
    assert f"expected containers (compose projects): {expected}" in result.stdout
    assert "API + Admin UI are host npm processes" in result.stdout


def test_unknown_profile_fails() -> None:
    result = subprocess.run(
        ["bash", str(STATUS_SH), "--profile", "oracle"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "unknown profile" in result.stderr


def test_package_json_has_profile_scripts_and_keeps_all() -> None:
    text = PACKAGE_JSON.read_text(encoding="utf-8")
    for name in (
        "local:containers:all:start",
        "local:containers:all:stop",
        "local:containers:all:status",
        "local:containers:sqlite:start",
        "local:containers:sqlite:stop",
        "local:containers:sqlite:status",
        "local:containers:postgres:start",
        "local:containers:postgres:stop",
        "local:containers:postgres:status",
        "local:containers:mongodb:start",
        "local:containers:mongodb:stop",
        "local:containers:mongodb:status",
        "local:containers:pgvector:start",
        "local:containers:pgvector:stop",
        "local:containers:pgvector:status",
        "local:containers:chroma:start",
        "local:containers:chroma:stop",
        "local:containers:chroma:status",
        "local:containers:redis:start",
        "local:containers:redis:stop",
        "local:containers:redis:status",
    ):
        assert name in text, name
    assert "docker-all-up.sh --profile sqlite" in text
    assert "docker-all-up.sh --profile postgres" in text
    assert "docker-all-up.sh --profile mongodb" in text
    assert "docker-all-up.sh --profile pgvector" in text
    assert "docker-all-up.sh --profile chroma" in text
    assert "docker-all-up.sh --profile redis" in text


def test_operational_postgres_compose_hosts_pgvector() -> None:
    compose = LOCAL / "postgres" / "docker-compose.yaml"
    assert compose.is_file()
    body = compose.read_text(encoding="utf-8")
    assert "cca-operational-postgres" in body
    assert "pgvector/pgvector:pg16" in body


def test_pgvector_compose_retired() -> None:
    assert not (LOCAL / "pgvector" / "docker-compose.yaml").is_file()
    readme = LOCAL / "pgvector" / "README.md"
    assert readme.is_file()
    assert "Retired" in readme.read_text(encoding="utf-8")


def test_chroma_and_redis_compose_exist() -> None:
    chroma = (LOCAL / "chroma" / "docker-compose.yaml").read_text(encoding="utf-8")
    redis = (LOCAL / "redis" / "docker-compose.yaml").read_text(encoding="utf-8")
    assert "cca-chroma" in chroma
    assert "chromadb/chroma" in chroma
    # Host 8100 by default — Middleware API owns :8000 (M10-0001 / #208)
    assert "CCA_CHROMA_PORT:-8100" in chroma
    assert "cca-redis-stack" in redis
    assert "redis/redis-stack" in redis
