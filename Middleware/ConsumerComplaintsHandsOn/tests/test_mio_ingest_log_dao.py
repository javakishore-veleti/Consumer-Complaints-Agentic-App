import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogRecord, MioIngestLogReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_ingest_log_dao as dao_impl
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> MioIngestLogCtx:
    return MioIngestLogCtx(req=MioIngestLogReq(**fields))


def _mio(name="t_mio") -> str:
    ctx = MioCtx(req=MioReq(name=name))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ingest(mio_id: str, **more) -> MioIngestLogRecord:
    ctx = _ctx(mio_id=mio_id, **more)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _ingest_rows(data_dir) -> list[tuple]:
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        return db.execute("select id, mio_id from mios_ingest_log").fetchall()


def _list(**fields) -> list[MioIngestLogRecord]:
    ctx = _ctx(**fields)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def _one_tick_per_call(monkeypatch):
    """Makes every _now() later than the one before, so the order of rows does not depend on the clock."""
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    ticks = (start + timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(dao_impl, "_now", lambda: next(ticks))


def test_create_starts_as_requested_with_empty_volume(data_dir):
    mio_id = _mio()
    row = _ingest(mio_id)
    assert len(row.id) == 36
    assert (row.mio_id, row.status) == (mio_id, "requested")
    assert (row.message, row.started_at, row.finished_at) == (None, None, None)
    assert (row.rows_loaded, row.batch_count, row.increment_marker) == (None, None, None)
    assert row.requested_at.tzinfo is not None


def test_create_stores_the_given_message_and_volume(data_dir):
    row = _ingest(_mio(), message="first load", rows_loaded=0, batch_count=3, increment_marker="2026-11-01")
    assert (row.message, row.rows_loaded, row.batch_count, row.increment_marker) == ("first load", 0, 3, "2026-11-01")
    fetched = _ctx(id=row.id)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(fetched) == SUCCESS
    assert fetched.resp.records == [row]


def test_create_stores_a_row_count_above_the_32_bit_range(data_dir):
    assert _ingest(_mio(), rows_loaded=5_000_000_000).rows_loaded == 5_000_000_000


def test_create_always_starts_as_requested_whatever_the_request_says(data_dir):
    assert _ingest(_mio(), status="completed").status == "requested"


def test_create_for_an_unknown_mio_is_not_found_and_stores_nothing(data_dir):
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(_ctx(mio_id="no-such-mio")) == NOT_FOUND
    assert _ingest_rows(data_dir) == []


@pytest.mark.parametrize(
    "fields",
    [
        {"mio_id": None},
        {"mio_id": ""},
        {"rows_loaded": True},
        {"rows_loaded": -1},
        {"rows_loaded": 1.5},
        {"rows_loaded": "10"},
        {"batch_count": False},
        {"batch_count": -2},
        {"batch_count": 2.0},
        {"increment_marker": "m" * 256},
        {"increment_marker": 20261101},
    ],
)
def test_create_rejects_a_missing_mio_id_or_an_invalid_volume_field(data_dir, fields):
    req = {"mio_id": _mio(), **fields}
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(_ctx(**req)) == INVALID_INPUT
    assert _ingest_rows(data_dir) == []


def test_create_accepts_a_marker_of_exactly_255_characters(data_dir):
    assert _ingest(_mio(), increment_marker="m" * 255).increment_marker == "m" * 255


def test_get_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    assert logs.get(_ctx()) == INVALID_INPUT
    assert logs.get(_ctx(id="no-such-row")) == NOT_FOUND


def test_list_of_an_empty_log_is_success_with_no_rows(data_dir):
    assert _list() == []


def test_list_is_newest_first(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    mio_id = _mio()
    first, second, third = (_ingest(mio_id) for _ in range(3))
    assert [r.id for r in _list()] == [third.id, second.id, first.id]


def test_list_filters_by_mio_and_status(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    three, six = _mio("t_three"), _mio("t_six")
    a = _ingest(three)
    b = _ingest(three)
    c = _ingest(six)
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute("update mios_ingest_log set status = 'started' where id = ?", (b.id,))  # update comes in a later task

    assert [r.id for r in _list(mio_id=three)] == [b.id, a.id]
    assert [r.id for r in _list(mio_id=six)] == [c.id]
    assert [r.id for r in _list(status="started")] == [b.id]
    assert [r.id for r in _list(status="requested")] == [c.id, a.id]
    assert [r.id for r in _list(mio_id=three, status="requested")] == [a.id]
    assert _list(mio_id="no-such-mio") == []
    assert _list(status="completed") == []


def test_list_limit_and_offset(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    mio_id = _mio()
    rows = [_ingest(mio_id) for _ in range(5)]
    newest_first = [r.id for r in reversed(rows)]
    assert [r.id for r in _list(limit=2)] == newest_first[:2]
    assert [r.id for r in _list(limit=2, offset=2)] == newest_first[2:4]
    assert [r.id for r in _list(offset=4)] == newest_first[4:]


def test_list_rejects_a_negative_limit_or_offset_and_an_unknown_status(data_dir):
    _ingest(_mio())
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    assert logs.list(_ctx(limit=-1)) == INVALID_INPUT
    assert logs.list(_ctx(offset=-1)) == INVALID_INPUT
    assert logs.list(_ctx(status="bogus")) == INVALID_INPUT
    zero = _ctx(limit=0)
    assert logs.list(zero) == SUCCESS and zero.resp.records == []


def test_create_reads_the_mio_inside_the_same_shared_transaction(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    new_mio = MioCtx(transaction=rolled_back, req=MioReq(name="t_inside"))
    assert DaoObjectsFactory.get_mio_dao().create(new_mio) == SUCCESS  # not committed: only this transaction sees it
    ingest = MioIngestLogCtx(transaction=rolled_back, req=MioIngestLogReq(mio_id=new_mio.resp.records[0].id))
    assert logs.create(ingest) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert _list() == []
    assert DaoObjectsFactory.get_mio_dao().get(MioCtx(req=MioReq(name="t_inside"))) == NOT_FOUND

    mio_id = _mio("t_kept")
    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    kept = MioIngestLogCtx(transaction=committed, req=MioIngestLogReq(mio_id=mio_id))
    assert logs.create(kept) == SUCCESS
    assert _list() == []  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert [r.id for r in _list()] == [kept.resp.records[0].id]
