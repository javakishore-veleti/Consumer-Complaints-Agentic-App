"""HTTP tests for /ingestion-logs/{zone} (M55-0011 / #391)."""


def _create(client, zone="curated", partition_key="p0"):
    return client.post(
        f"/ingestion-logs/{zone}",
        json={
            "partition_key": partition_key,
            "data_tech": "iceberg",
            "source_end_point_id": "src-1",
            "dest_end_point_id": "dst-1",
        },
    )


def test_create_list_claim_complete(client):
    for i in range(3):
        r = _create(client, partition_key=f"k{i}")
        assert r.status_code == 201, r.text

    listed = client.get("/ingestion-logs/curated", params={"limit": 30})
    assert listed.status_code == 200
    assert len(listed.json()) == 3
    assert listed.json()[0]["partition_key"] == "k2"

    claimed = client.post("/ingestion-logs/curated/claim", json={"limit": 2})
    assert claimed.status_code == 200
    body = claimed.json()
    assert len(body) == 2
    assert all(row["status"] == "in_progress" for row in body)

    done = client.post(
        f"/ingestion-logs/curated/{body[0]['id']}/complete",
        json={"status": "done"},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "done"


def test_list_filters_workflow_execution_id(client):
    r = _create(client, partition_key="wf")
    assert r.status_code == 201
    row_id = r.json()["id"]
    upd = client.put(
        f"/ingestion-logs/curated/{row_id}",
        json={"workflow_execution_id": "exec-99"},
    )
    assert upd.status_code == 200
    filtered = client.get("/ingestion-logs/curated", params={"workflow_execution_id": "exec-99"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["workflow_execution_id"] == "exec-99"


def test_openapi_includes_ingestion_logs(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/ingestion-logs/{zone}" in paths
    assert "/ingestion-logs/{zone}/claim" in paths
