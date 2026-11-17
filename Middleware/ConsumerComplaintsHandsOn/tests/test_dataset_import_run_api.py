"""HTTP tests for dataset import run callbacks + list (M11)."""


SECRET = "s3cret-value-for-tests"
HEADERS = {"X-Callback-Secret": SECRET}
STARTED = "2026-11-14T15:18:00Z"


def test_callback_create_land_and_list_eligible(client, monkeypatch, data_dir):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    created = client.post(
        "/callbacks/dataset-import-runs",
        headers=HEADERS,
        json={
            "id": "11111111-1111-1111-1111-111111111111",
            "run_folder_name": "2026-11-14-15-18-00",
            "location_kind": "local_path",
            "location_ref": "/data/cfpb/2026-11-14-15-18-00",
            "source_snapshot_start": STARTED,
            "source_snapshot_end": STARTED,
            "workflow_started_at": STARTED,
            "status": "staging",
            "execution_id": "exec-1",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["id"] == "11111111-1111-1111-1111-111111111111"
    assert body["status"] == "staging"

    landed = client.patch(
        "/callbacks/dataset-import-runs/11111111-1111-1111-1111-111111111111",
        headers=HEADERS,
        json={
            "status": "landed",
            "workflow_completed_at": "2026-11-14T15:20:00Z",
            "part_count": 2,
        },
    )
    assert landed.status_code == 200, landed.text
    assert landed.json()["status"] == "landed"
    assert landed.json()["part_count"] == 2

    listed = client.get("/dataset-import-runs?eligible_only=true")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["run_folder_name"] == "2026-11-14-15-18-00"


def test_callback_requires_secret(client, data_dir):
    response = client.post(
        "/callbacks/dataset-import-runs",
        json={
            "run_folder_name": "2026-11-14-15-18-00",
            "location_kind": "local_path",
            "location_ref": "/x",
            "source_snapshot_start": STARTED,
            "source_snapshot_end": STARTED,
            "workflow_started_at": STARTED,
        },
    )
    assert response.status_code == 401
