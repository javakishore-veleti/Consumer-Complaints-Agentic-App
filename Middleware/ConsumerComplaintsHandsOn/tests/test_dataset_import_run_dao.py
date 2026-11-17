"""Tests for DatasetImportRunDao (M11 #230)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.common.dtos.dataset_import_run_dtos import (
    LOCATION_LOCAL_PATH,
    STATUS_FAILED,
    STATUS_INGESTED,
    STATUS_INGESTING,
    STATUS_LANDED,
    STATUS_STAGING,
    DatasetImportRunCtx,
    DatasetImportRunRecord,
    DatasetImportRunReq,
)
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

STARTED = datetime(2026, 11, 14, 15, 18, 0, tzinfo=UTC)


def _ctx(**fields) -> DatasetImportRunCtx:
    return DatasetImportRunCtx(req=DatasetImportRunReq(**fields))


def _dao():
    return DaoObjectsFactory.get_dataset_import_run_dao()


def _create(**overrides) -> DatasetImportRunRecord:
    fields = {
        "run_folder_name": "2026-11-14-15-18-00",
        "location_kind": LOCATION_LOCAL_PATH,
        "location_ref": "/data/cfpb/2026-11-14-15-18-00",
        "source_snapshot_start": STARTED,
        "source_snapshot_end": STARTED,
        "workflow_started_at": STARTED,
        "status": STATUS_STAGING,
    }
    fields.update(overrides)
    ctx = _ctx(**fields)
    assert _dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def test_create_staging_row(data_dir):
    row = _create()
    assert len(row.id) == 36
    assert row.status == STATUS_STAGING
    assert row.run_folder_name == "2026-11-14-15-18-00"
    assert row.location_kind == LOCATION_LOCAL_PATH
    assert row.ingested_at is None
    assert row.created_at.tzinfo is not None


def test_create_rejects_missing_required_fields(data_dir):
    assert _dao().create(_ctx(run_folder_name="x")) == INVALID_INPUT
    assert _dao().create(_ctx()) == INVALID_INPUT


def test_create_duplicate_folder_is_conflict(data_dir):
    _create()
    assert (
        _dao().create(
            _ctx(
                run_folder_name="2026-11-14-15-18-00",
                location_kind=LOCATION_LOCAL_PATH,
                location_ref="/other",
                source_snapshot_start=STARTED,
                source_snapshot_end=STARTED,
                workflow_started_at=STARTED,
            )
        )
        == CONFLICT
    )


def test_get_and_list_newest_first(data_dir):
    older = _create(run_folder_name="2026-11-14-15-18-00")
    newer = _create(
        run_folder_name="2026-11-14-16-00-00",
        location_ref="/data/cfpb/2026-11-14-16-00-00",
        workflow_started_at=STARTED + timedelta(hours=1),
        source_snapshot_start=STARTED + timedelta(hours=1),
        source_snapshot_end=STARTED + timedelta(hours=1),
    )
    got = _ctx(id=older.id)
    assert _dao().get(got) == SUCCESS
    assert got.resp.records[0].id == older.id

    listed = _ctx()
    assert _dao().list(listed) == SUCCESS
    assert [r.id for r in listed.resp.records] == [newer.id, older.id]


def test_get_unknown_and_missing_id(data_dir):
    assert _dao().get(_ctx()) == INVALID_INPUT
    assert _dao().get(_ctx(id="no-such")) == NOT_FOUND


def test_land_then_ingest_happy_path(data_dir):
    row = _create()
    land = _ctx(
        id=row.id,
        status=STATUS_LANDED,
        workflow_completed_at=STARTED + timedelta(minutes=5),
        part_count=3,
    )
    assert _dao().update(land) == SUCCESS
    assert land.resp.records[0].status == STATUS_LANDED
    assert land.resp.records[0].part_count == 3

    start = _ctx(id=row.id, status=STATUS_INGESTING)
    assert _dao().update(start) == SUCCESS
    assert start.resp.records[0].status == STATUS_INGESTING

    done = _ctx(id=row.id, status=STATUS_INGESTED)
    assert _dao().update(done) == SUCCESS
    assert done.resp.records[0].status == STATUS_INGESTED
    assert done.resp.records[0].ingested_at is not None


def test_illegal_transition_is_conflict(data_dir):
    row = _create()
    assert _dao().update(_ctx(id=row.id, status=STATUS_INGESTED)) == CONFLICT
    assert _dao().update(_ctx(id=row.id, status=STATUS_INGESTING)) == CONFLICT


def test_failed_can_retry_ingest(data_dir):
    row = _create(status=STATUS_LANDED)
    assert _dao().update(_ctx(id=row.id, status=STATUS_FAILED, message="boom")) == SUCCESS
    assert _dao().update(_ctx(id=row.id, status=STATUS_INGESTING)) == SUCCESS


def test_eligible_only_lists_landed_and_failed(data_dir):
    landed = _create(run_folder_name="2026-11-14-15-18-00", status=STATUS_LANDED)
    failed = _create(
        run_folder_name="2026-11-14-15-19-00",
        location_ref="/data/cfpb/failed",
        workflow_started_at=STARTED + timedelta(minutes=1),
        source_snapshot_start=STARTED,
        source_snapshot_end=STARTED,
        status=STATUS_FAILED,
    )
    ingested = _create(
        run_folder_name="2026-11-14-15-20-00",
        location_ref="/data/cfpb/done",
        workflow_started_at=STARTED + timedelta(minutes=2),
        source_snapshot_start=STARTED,
        source_snapshot_end=STARTED,
        status=STATUS_LANDED,
    )
    assert _dao().update(_ctx(id=ingested.id, status=STATUS_INGESTING)) == SUCCESS
    assert _dao().update(_ctx(id=ingested.id, status=STATUS_INGESTED)) == SUCCESS
    _create(
        run_folder_name="2026-11-14-15-21-00",
        location_ref="/data/cfpb/staging",
        workflow_started_at=STARTED + timedelta(minutes=3),
        source_snapshot_start=STARTED,
        source_snapshot_end=STARTED,
        status=STATUS_STAGING,
    )

    eligible = _ctx(eligible_only=True)
    assert _dao().list(eligible) == SUCCESS
    ids = {r.id for r in eligible.resp.records}
    assert ids == {landed.id, failed.id}


@pytest.mark.parametrize("bad", [-1, True])
def test_list_rejects_bad_paging(data_dir, bad):
    assert _dao().list(_ctx(limit=bad)) == INVALID_INPUT
    assert _dao().list(_ctx(offset=bad)) == INVALID_INPUT
