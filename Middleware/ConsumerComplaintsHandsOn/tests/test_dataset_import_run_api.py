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


def test_comment_and_tags_http(client, monkeypatch, data_dir):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    created = client.post(
        "/callbacks/dataset-import-runs",
        headers=HEADERS,
        json={
            "id": "22222222-2222-2222-2222-222222222222",
            "run_folder_name": "2026-11-14-15-18-00",
            "location_kind": "local_path",
            "location_ref": "/data/cfpb/2026-11-14-15-18-00",
            "source_snapshot_start": STARTED,
            "source_snapshot_end": STARTED,
            "workflow_started_at": STARTED,
            "status": "landed",
            "comment": "seed comment",
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["comment"] == "seed comment"
    import_id = created.json()["id"]

    patched = client.patch(
        f"/dataset-import-runs/{import_id}",
        json={"comment": "ops note"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["comment"] == "ops note"

    added = client.post(
        f"/dataset-import-runs/{import_id}/tags",
        json={"tags": ["alpha", "beta", "alpha"]},
    )
    assert added.status_code == 200, added.text
    assert [t["tag"] for t in added.json()] == ["alpha", "beta"]

    listed = client.get(f"/dataset-import-runs/{import_id}/tags")
    assert listed.status_code == 200
    assert [t["tag"] for t in listed.json()] == ["alpha", "beta"]

    other = client.post(
        "/callbacks/dataset-import-runs",
        headers=HEADERS,
        json={
            "id": "33333333-3333-3333-3333-333333333333",
            "run_folder_name": "2026-11-14-16-00-00",
            "location_kind": "local_path",
            "location_ref": "/data/cfpb/other",
            "source_snapshot_start": STARTED,
            "source_snapshot_end": STARTED,
            "workflow_started_at": "2026-11-14T16:00:00Z",
            "status": "landed",
        },
    )
    assert other.status_code == 200, other.text
    other_id = other.json()["id"]
    assert (
        client.post(
            f"/dataset-import-runs/{other_id}/tags",
            json={"tags": ["beta"]},
        ).status_code
        == 200
    )

    filtered = client.get("/dataset-import-runs", params={"tag": "alpha"})
    assert filtered.status_code == 200
    assert [r["id"] for r in filtered.json()] == [import_id]

    both = client.get("/dataset-import-runs", params={"tag": "beta"})
    assert {r["id"] for r in both.json()} == {import_id, other_id}
