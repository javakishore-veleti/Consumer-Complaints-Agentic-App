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


# ---- update (D30) ----


def _update(row_id: str, **fields) -> tuple[int, MioIngestLogCtx]:
    ctx = _ctx(id=row_id, **fields)
    return DaoObjectsFactory.get_mio_ingest_log_dao().update(ctx), ctx


def _stored(row_id: str) -> MioIngestLogRecord:
    ctx = _ctx(id=row_id)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def test_requested_to_started_sets_started_at_and_the_notes(data_dir):
    row = _ingest(_mio())
    code, ctx = _update(row.id, status="started", message="picked up", batch_count=4)
    assert code == SUCCESS
    started = ctx.resp.records[0]
    assert (started.status, started.message, started.batch_count) == ("started", "picked up", 4)
    assert started.started_at is not None and started.started_at.tzinfo is not None
    assert started.finished_at is None
    assert _stored(row.id) == started


def test_started_to_completed_sets_finished_at_keeps_started_at_and_stores_the_volume(data_dir):
    row = _ingest(_mio())
    started = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="completed", rows_loaded=1200, increment_marker="2026-11-13")
    assert code == SUCCESS
    done = ctx.resp.records[0]
    assert done.status == "completed"
    assert done.started_at == started.started_at
    assert done.finished_at is not None and done.finished_at >= done.started_at
    assert (done.rows_loaded, done.increment_marker) == (1200, "2026-11-13")


def test_requested_to_failed_sets_finished_at_and_leaves_started_at_empty(data_dir):
    row = _ingest(_mio())
    code, ctx = _update(row.id, status="failed", message="could not start")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert (failed.status, failed.message) == ("failed", "could not start")
    assert failed.started_at is None and failed.finished_at is not None


def test_started_then_failed_is_a_legal_path(data_dir):
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    code, ctx = _update(row.id, status="failed", message="batch 3 failed")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert failed.status == "failed" and failed.started_at is not None and failed.finished_at is not None


@pytest.mark.parametrize(
    "path, bad",
    [
        ((), "completed"),
        (("started",), "requested"),
        (("started", "completed"), "started"),
        (("started", "completed"), "failed"),
        (("started", "completed"), "requested"),
        (("failed",), "started"),
        (("failed",), "completed"),
        (("failed",), "requested"),
    ],
)
def test_an_illegal_move_is_a_conflict_and_changes_nothing(data_dir, path, bad):
    row = _ingest(_mio())
    for status in path:
        assert _update(row.id, status=status)[0] == SUCCESS
    before = _stored(row.id)
    code, _ = _update(row.id, status=bad, message="must not be stored", rows_loaded=99, increment_marker="no")
    assert code == CONFLICT
    assert _stored(row.id) == before


def test_the_same_status_again_is_accepted_and_changes_no_time(data_dir):
    row = _ingest(_mio())
    first = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="started", message="retry of the callback")
    assert code == SUCCESS
    again = ctx.resp.records[0]
    assert again.started_at == first.started_at and again.finished_at is None
    assert again.message == "retry of the callback"


def test_update_without_a_status_changes_only_the_given_fields(data_dir):
    row = _ingest(_mio(), message="kept", batch_count=2)
    code, ctx = _update(row.id, rows_loaded=10)
    assert code == SUCCESS
    after = ctx.resp.records[0]
    assert (after.status, after.message, after.batch_count, after.rows_loaded) == ("requested", "kept", 2, 10)


def test_a_final_row_keeps_its_status_and_times_but_still_accepts_the_notes_and_volume(data_dir):
    # D30 protects the status and the times; the message and the volume are notes a late callback may still fill in.
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    done = _update(row.id, status="completed")[1].resp.records[0]
    code, ctx = _update(
        row.id, status="completed", message="late note", rows_loaded=5000, batch_count=7, increment_marker="offset:5000"
    )
    assert code == SUCCESS
    after = ctx.resp.records[0]
    assert (after.status, after.started_at, after.finished_at) == (done.status, done.started_at, done.finished_at)
    assert (after.message, after.rows_loaded, after.batch_count, after.increment_marker) == (
        "late note",
        5000,
        7,
        "offset:5000",
    )
    code, ctx = _update(row.id, rows_loaded=5001)  # no status at all on a final row
    assert code == SUCCESS and ctx.resp.records[0].rows_loaded == 5001


def test_update_never_changes_the_mio(data_dir):
    mio_id = _mio()
    row = _ingest(mio_id)
    code, ctx = _update(row.id, mio_id=_mio("t_other"), status="started")
    assert code == SUCCESS
    assert ctx.resp.records[0].mio_id == mio_id
    assert _stored(row.id).mio_id == mio_id


def test_a_stale_second_update_after_completed_is_a_conflict(data_dir):
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    assert _update(row.id, status="completed", rows_loaded=10)[0] == SUCCESS
    done = _stored(row.id)
    assert _update(row.id, status="failed", rows_loaded=0)[0] == CONFLICT  # a callback that arrives late
    assert _stored(row.id) == done


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "bogus"},
        {"rows_loaded": True},
        {"rows_loaded": -1},
        {"rows_loaded": 2.5},
        {"batch_count": -1},
        {"batch_count": True},
        {"increment_marker": "m" * 256},
        {"increment_marker": 7},
    ],
)
def test_update_rejects_an_unknown_status_or_an_invalid_volume_field(data_dir, fields):
    row = _ingest(_mio())
    assert _update(row.id, **fields)[0] == INVALID_INPUT
    assert _stored(row.id) == row


def test_update_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    assert DaoObjectsFactory.get_mio_ingest_log_dao().update(_ctx(status="started")) == INVALID_INPUT
    assert _update("no-such-row", status="started")[0] == NOT_FOUND


def test_a_rival_move_made_after_the_read_is_not_overwritten(data_dir, monkeypatch):
    # _now() runs after update has read the row and before it writes, so a rival callback that commits inside it
    # is exactly the race: two callbacks both read "started".
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="failed", message="rival")[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, _ = _update(row.id, status="completed", message="loser", rows_loaded=42)
    assert code == CONFLICT
    stored = _stored(row.id)
    assert (stored.status, stored.message, stored.rows_loaded) == ("failed", "rival", None)  # the loser changed nothing
    assert stored.finished_at is not None


def test_a_rival_that_made_the_same_move_first_is_accepted_like_a_retry(data_dir, monkeypatch):
    row = _ingest(_mio())
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="started", batch_count=3)[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, ctx = _update(row.id, status="started", message="mine")
    assert code == SUCCESS
    result = ctx.resp.records[0]
    assert (result.status, result.message, result.batch_count) == ("started", "mine", 3)
    assert result == _stored(row.id)
    assert result.started_at is not None  # the rival's time, set once


def test_an_update_inside_a_rolled_back_transaction_leaves_no_trace(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()
    row = _ingest(_mio())
    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    moved = MioIngestLogCtx(transaction=tx, req=MioIngestLogReq(id=row.id, status="started", rows_loaded=8))
    assert logs.update(moved) == SUCCESS
    assert moved.resp.records[0].status == "started"
    assert transactions.rollback(tx) == SUCCESS
    assert _stored(row.id) == row
