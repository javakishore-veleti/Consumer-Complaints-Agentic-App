"""DAO tests for zone ingest_log_* (M55-0011 / #391)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.common.dtos.zone_ingest_log_dtos import ZoneIngestLogCtx, ZoneIngestLogReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


@pytest.fixture
def dao(data_dir):
    DaoObjectsFactory.reset()
    return DaoObjectsFactory.get_zone_ingest_log_dao()


def _req(**kwargs) -> ZoneIngestLogReq:
    base = dict(
        zone="curated",
        partition_key="p0",
        data_tech="iceberg",
        source_end_point_id="src-1",
        dest_end_point_id="dst-1",
    )
    base.update(kwargs)
    return ZoneIngestLogReq(**base)


def test_create_get_list_newest_first(dao):
    older = ZoneIngestLogCtx(req=_req(partition_key="a"))
    assert dao.create(older) == SUCCESS
    newer = ZoneIngestLogCtx(req=_req(partition_key="b"))
    assert dao.create(newer) == SUCCESS

    listed = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", limit=30))
    assert dao.list(listed) == SUCCESS
    assert [r.partition_key for r in listed.resp.records] == ["b", "a"]
    assert all(r.status == "pending" for r in listed.resp.records)

    got = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=older.resp.records[0].id))
    assert dao.get(got) == SUCCESS
    assert got.resp.records[0].partition_key == "a"


def test_list_clamps_limit_to_30(dao):
    for i in range(35):
        assert dao.create(ZoneIngestLogCtx(req=_req(partition_key=f"k{i}"))) == SUCCESS
    listed = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", limit=100))
    assert dao.list(listed) == SUCCESS
    assert len(listed.resp.records) == 30


def test_claim_pending_caps_at_five_and_is_idempotent_across_calls(dao):
    for i in range(8):
        assert dao.create(ZoneIngestLogCtx(req=_req(partition_key=f"c{i}"))) == SUCCESS

    first = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", claim_limit=5))
    assert dao.claim_pending(first) == SUCCESS
    assert len(first.resp.records) == 5
    assert all(r.status == "in_progress" for r in first.resp.records)

    second = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", claim_limit=5))
    assert dao.claim_pending(second) == SUCCESS
    assert len(second.resp.records) == 3
    claimed_ids = {r.id for r in first.resp.records} | {r.id for r in second.resp.records}
    assert len(claimed_ids) == 8


def test_complete_and_reset_failed(dao):
    created = ZoneIngestLogCtx(req=_req(partition_key="x"))
    assert dao.create(created) == SUCCESS
    row_id = created.resp.records[0].id

    claim = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", claim_limit=1))
    assert dao.claim_pending(claim) == SUCCESS

    bad = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=row_id, status="pending"))
    assert dao.complete(bad) == INVALID_INPUT

    fail = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=row_id, status="failed", configs_json='{"e":1}'))
    assert dao.complete(fail) == SUCCESS
    assert fail.resp.records[0].status == "failed"

    reset = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=row_id))
    assert dao.reset_failed(reset) == SUCCESS
    assert reset.resp.records[0].status == "pending"

    done_row = ZoneIngestLogCtx(req=_req(partition_key="y"))
    assert dao.create(done_row) == SUCCESS
    done_id = done_row.resp.records[0].id
    assert dao.claim_pending(ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", claim_limit=5))) == SUCCESS
    assert (
        dao.complete(ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=done_id, status="done")))
        == SUCCESS
    )
    assert dao.reset_failed(ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="curated", id=done_id))) == CONFLICT


def test_delete_and_unknown_zone(dao):
    created = ZoneIngestLogCtx(req=_req(zone="raw", partition_key="r1"))
    assert dao.create(created) == SUCCESS
    row_id = created.resp.records[0].id
    assert dao.delete(ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="raw", id=row_id))) == SUCCESS
    assert dao.get(ZoneIngestLogCtx(req=ZoneIngestLogReq(zone="raw", id=row_id))) == NOT_FOUND
    assert dao.create(ZoneIngestLogCtx(req=_req(zone="nope"))) == INVALID_INPUT


def test_duplicate_unique_key_is_conflict(dao):
    assert dao.create(ZoneIngestLogCtx(req=_req(partition_key="dup"))) == SUCCESS
    assert dao.create(ZoneIngestLogCtx(req=_req(partition_key="dup"))) == CONFLICT
