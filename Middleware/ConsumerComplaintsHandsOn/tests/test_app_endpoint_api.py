"""HTTP tests for GET /app-endpoints (#156)."""

SEEDED_ID = "ccbce57d-bd9f-56fe-a258-fa2deb9dd393"


def test_list_app_endpoints_returns_seed_without_secret_values(client):
    response = client.get("/app-endpoints")
    assert response.status_code == 200
    body = response.json()
    assert any(e["id"] == SEEDED_ID and e["name"] == "cfpb_source_http_to_local" for e in body)
    assert all("value" not in e for e in body)
    assert all("password" not in e for e in body)


def test_list_filter_by_category(client):
    response = client.get("/app-endpoints", params={"category": "source"})
    assert response.status_code == 200
    assert all(e["category"] == "source" for e in response.json())


def test_get_app_endpoint_by_id(client):
    response = client.get(f"/app-endpoints/{SEEDED_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == SEEDED_ID
    assert body["from_env_var_name"] is None
    assert body.get("credentials_ref") is None


def test_get_unknown_app_endpoint_is_404(client):
    response = client.get("/app-endpoints/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
