"""GET/POST /intellect/risk-radar (M53-0001 / #359)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN = REPO_ROOT / "CICD" / "Local" / "iceberg" / "golden" / "risk_radar_golden_3m.json"


def test_risk_radar_fixture_get(client):
    response = client.get("/intellect/risk-radar")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fixture"
    assert len(body["alerts"]) >= 1
    alert = body["alerts"][0]
    assert alert["id"]
    assert alert["drilldown_ast"]["table"]
    assert alert["k_anon_ok"] is True


def test_risk_radar_fixture_post(client):
    response = client.post("/intellect/risk-radar", json={"source": "fixture"})
    assert response.status_code == 200
    assert response.json()["alerts"][0]["id"] == "rr1-capital-one-credit-cards"


def test_risk_radar_bad_source_is_422(client):
    response = client.post("/intellect/risk-radar", json={"source": "nope"})
    assert response.status_code == 422


def test_risk_radar_warehouse_without_container_is_503(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.services.impl.risk_radar_service_impl._container_running",
        lambda req: False,
    )
    response = client.post("/intellect/risk-radar", json={"source": "warehouse"})
    assert response.status_code == 503


def test_openapi_includes_risk_radar(client):
    spec = client.get("/openapi.json").json()
    assert "/intellect/risk-radar" in spec["paths"]


def test_golden_fixture_exists():
    assert GOLDEN.is_file()
