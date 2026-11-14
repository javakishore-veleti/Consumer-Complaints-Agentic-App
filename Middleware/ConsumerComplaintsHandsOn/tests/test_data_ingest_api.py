def test_create_get_list_update_delete(client):
    created = client.post("/data-ingest-logs", json={"purpose": "download_3_months"})
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "requested"
    log_id = body["id"]

    assert client.get(f"/data-ingest-logs/{log_id}").json() == body
    assert [r["id"] for r in client.get("/data-ingest-logs").json()] == [log_id]
    assert client.get("/data-ingest-logs", params={"status_": "started"}).json() == []

    updated = client.patch(f"/data-ingest-logs/{log_id}", json={"status": "started", "run_id": "run-1"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "started"
    assert updated.json()["started_at"] is not None

    assert client.delete(f"/data-ingest-logs/{log_id}").status_code == 204
    assert client.get(f"/data-ingest-logs/{log_id}").status_code == 404


def test_not_found(client):
    assert client.get("/data-ingest-logs/nope").status_code == 404
    assert client.patch("/data-ingest-logs/nope", json={"status": "started"}).status_code == 404
    assert client.delete("/data-ingest-logs/nope").status_code == 404


def test_invalid_input_is_rejected(client):
    assert client.post("/data-ingest-logs", json={"purpose": "   "}).status_code == 422  # facade rule
    assert client.post("/data-ingest-logs", json={"purpose": "x", "status": "bogus"}).status_code == 422  # body schema
    log_id = client.post("/data-ingest-logs", json={"purpose": "x"}).json()["id"]
    assert client.patch(f"/data-ingest-logs/{log_id}", json={}).status_code == 422  # nothing to change
    assert client.get("/data-ingest-logs", params={"limit": 0}).status_code == 422
    assert client.get("/data-ingest-logs", params={"limit": 100000}).status_code == 422


def test_openapi_lists_the_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) >= {"/data-ingest-logs", "/data-ingest-logs/{log_id}", "/health"}


def test_out_of_order_status_is_409_and_duplicates_are_fine(client):
    log_id = client.post("/data-ingest-logs", json={"purpose": "x"}).json()["id"]
    assert client.patch(f"/data-ingest-logs/{log_id}", json={"status": "completed"}).status_code == 409
    assert client.patch(f"/data-ingest-logs/{log_id}", json={"status": "started"}).status_code == 200
    assert client.patch(f"/data-ingest-logs/{log_id}", json={"status": "started"}).status_code == 200
    assert client.patch(f"/data-ingest-logs/{log_id}", json={"status": "completed"}).status_code == 200
    assert client.patch(f"/data-ingest-logs/{log_id}", json={"status": "failed"}).status_code == 409


def test_a_row_is_always_created_as_requested(client):
    assert client.post("/data-ingest-logs", json={"purpose": "x", "status": "started"}).status_code == 422
    assert client.post("/data-ingest-logs", json={"purpose": "x", "status": "requested"}).status_code == 201
