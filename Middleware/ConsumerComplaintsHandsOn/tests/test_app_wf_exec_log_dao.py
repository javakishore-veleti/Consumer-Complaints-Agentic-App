import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord, AppWfExecLogReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_app_wf_exec_log_dao as dao_impl
from app.core.dao.objects_factory import DaoObjectsFactory

CONFIG = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "dry_run": False, "limit": None}


def _ctx(**fields) -> AppWfExecLogCtx:
    return AppWfExecLogCtx(req=AppWfExecLogReq(**fields))


def _workflow(name="download_3_months", engine_type="apache_airflow", engine_workflow_id="download_dag", **more) -> AppWfRecord:
    ctx = AppWfCtx(
        req=AppWfReq(workflow_name=name, engine_type=engine_type, engine_workflow_id=engine_workflow_id, **more)
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _execute(workflow_id: str, **more) -> AppWfExecLogRecord:
    ctx = _ctx(workflow_id=workflow_id, **more)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _exec_log_rows(data_dir) -> list[tuple]:
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        return db.execute("select id, config_used from app_workflows_exec_log").fetchall()


def test_create_copies_the_workflow_and_starts_as_requested(data_dir):
    workflow = _workflow(config=CONFIG)
    row = _execute(workflow.id)
    assert len(row.id) == 36
    assert row.workflow_id == workflow.id
    assert (row.workflow_name, row.engine_type, row.engine_workflow_id) == (
        "download_3_months",
        "apache_airflow",
        "download_dag",
    )
    assert row.config_used == CONFIG
    assert row.status == "requested"
    assert (row.engine_run_id, row.message, row.started_at, row.finished_at) == (None, None, None, None)
    assert row.requested_at.tzinfo is not None


def test_a_workflow_without_config_gives_a_null_config_used(data_dir):
    row = _execute(_workflow().id)
    assert row.config_used is None
    assert [r[1] for r in _exec_log_rows(data_dir)] == [None]  # SQL NULL, not "null" and not {}


def test_create_always_starts_as_requested_whatever_the_request_says(data_dir):
    assert _execute(_workflow().id, status="completed").status == "requested"


def test_create_accepts_a_disabled_workflow(data_dir):
    # Whether a disabled workflow may start is policy for the start endpoint (#42), not the DAO.
    assert _execute(_workflow(enabled=False).id).status == "requested"


def test_create_without_a_workflow_id_is_invalid_input(data_dir):
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(_ctx()) == INVALID_INPUT
    assert _exec_log_rows(data_dir) == []


def test_create_for_an_unknown_workflow_is_not_found_and_stores_nothing(data_dir):
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(_ctx(workflow_id="no-such-workflow")) == NOT_FOUND
    assert _exec_log_rows(data_dir) == []


def test_the_row_keeps_the_old_details_after_the_workflow_is_renamed_or_deleted(data_dir):
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    workflow = _workflow(config=CONFIG)
    first = _execute(workflow.id)

    renamed = AppWfCtx(
        req=AppWfReq(
            id=workflow.id, workflow_name="renamed", engine_workflow_id="other_dag", config={"retries": 9}
        )
    )
    assert workflows.update(renamed) == SUCCESS
    again = _ctx(id=first.id)
    assert logs.get(again) == SUCCESS
    old = again.resp.records[0]
    assert (old.workflow_name, old.engine_workflow_id, old.config_used) == ("download_3_months", "download_dag", CONFIG)

    second = _execute(workflow.id)  # an execution after the change sees the new details
    assert (second.workflow_name, second.engine_workflow_id, second.config_used) == (
        "renamed",
        "other_dag",
        {"retries": 9},
    )

    assert workflows.delete(AppWfCtx(req=AppWfReq(id=workflow.id))) == SUCCESS
    gone = _ctx(id=first.id)
    assert logs.get(gone) == SUCCESS
    assert gone.resp.records[0] == old
    assert gone.resp.records[0].workflow_id == workflow.id  # the id stays even though the workflow is gone


def test_get_returns_the_row_by_id(data_dir):
    row = _execute(_workflow().id)
    fetched = _ctx(id=row.id)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(fetched) == SUCCESS
    assert fetched.resp.records == [row]


def test_get_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.get(_ctx()) == INVALID_INPUT
    assert logs.get(_ctx(id="no-such-row")) == NOT_FOUND


def _update(row_id: str, **fields) -> tuple[int, AppWfExecLogCtx]:
    ctx = _ctx(id=row_id, **fields)
    return DaoObjectsFactory.get_app_wf_exec_log_dao().update(ctx), ctx


def _stored(row_id: str) -> AppWfExecLogRecord:
    ctx = _ctx(id=row_id)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def test_requested_to_started_sets_started_at_run_id_and_message(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, status="started", engine_run_id="manual__2026-11-14", message="picked up")
    assert code == SUCCESS
    started = ctx.resp.records[0]
    assert (started.status, started.engine_run_id, started.message) == ("started", "manual__2026-11-14", "picked up")
    assert started.started_at is not None and started.started_at.tzinfo is not None
    assert started.finished_at is None
    assert (started.workflow_name, started.engine_type, started.engine_workflow_id) == (
        row.workflow_name,
        row.engine_type,
        row.engine_workflow_id,
    )
    assert _stored(row.id) == started


def test_started_to_completed_sets_finished_at_and_keeps_started_at(data_dir):
    row = _execute(_workflow().id)
    started = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="completed")
    assert code == SUCCESS
    done = ctx.resp.records[0]
    assert done.status == "completed"
    assert done.started_at == started.started_at
    assert done.finished_at is not None and done.finished_at >= done.started_at


def test_requested_to_failed_sets_finished_at_and_leaves_started_at_empty(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, status="failed", message="could not start")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert (failed.status, failed.message) == ("failed", "could not start")
    assert failed.started_at is None and failed.finished_at is not None


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
    row = _execute(_workflow().id)
    for status in path:
        assert _update(row.id, status=status)[0] == SUCCESS
    before = _stored(row.id)
    code, _ = _update(row.id, status=bad, message="must not be stored", engine_run_id="must-not-be-stored")
    assert code == CONFLICT
    assert _stored(row.id) == before


def test_a_stale_second_update_after_completed_is_a_conflict(data_dir):
    row = _execute(_workflow().id)
    assert _update(row.id, status="started")[0] == SUCCESS
    assert _update(row.id, status="completed")[0] == SUCCESS
    done = _stored(row.id)
    assert _update(row.id, status="failed")[0] == CONFLICT  # a callback that arrives late
    assert _stored(row.id) == done


def test_the_same_status_again_is_accepted_and_changes_no_time(data_dir):
    row = _execute(_workflow().id)
    first = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="started", message="retry of the callback")
    assert code == SUCCESS
    again = ctx.resp.records[0]
    assert again.started_at == first.started_at and again.finished_at is None
    assert again.message == "retry of the callback"


def test_update_without_a_status_changes_only_the_given_fields(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, engine_run_id="run-1")
    assert code == SUCCESS
    assert (ctx.resp.records[0].status, ctx.resp.records[0].engine_run_id) == ("requested", "run-1")


def test_update_rejects_bad_input(data_dir):
    row = _execute(_workflow().id)
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.update(_ctx(status="started")) == INVALID_INPUT  # no id
    assert _update(row.id, status="bogus")[0] == INVALID_INPUT
    assert _update(row.id, engine_run_id="r" * 129)[0] == INVALID_INPUT
    assert _update(row.id, engine_run_id="r" * 128)[0] == SUCCESS
    assert _stored(row.id).status == "requested"


def test_update_of_an_unknown_row_is_not_found(data_dir):
    assert _update("no-such-row", status="started")[0] == NOT_FOUND


def _list(**fields) -> list[AppWfExecLogRecord]:
    ctx = _ctx(**fields)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def _one_tick_per_call(monkeypatch):
    """Makes every _now() later than the one before, so the order of rows does not depend on the clock."""
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    ticks = (start + timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(dao_impl, "_now", lambda: next(ticks))


def test_list_of_an_empty_log_is_success_with_no_rows(data_dir):
    assert _list() == []


def test_list_is_newest_first(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    workflow = _workflow()
    first, second, third = (_execute(workflow.id) for _ in range(3))
    assert [r.id for r in _list()] == [third.id, second.id, first.id]


def test_list_filters_by_workflow_status_and_engine_type(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    download = _workflow("download")
    steps = _workflow("steps", engine_type="aws_step_functions", engine_workflow_id="arn:sm")
    a = _execute(download.id)
    b = _execute(download.id)
    c = _execute(steps.id)
    assert _update(b.id, status="started")[0] == SUCCESS

    assert {r.id for r in _list(workflow_id=download.id)} == {a.id, b.id}
    assert [r.id for r in _list(workflow_id=steps.id)] == [c.id]
    assert [r.id for r in _list(status="started")] == [b.id]
    assert {r.id for r in _list(status="requested")} == {a.id, c.id}
    assert [r.id for r in _list(engine_type="aws_step_functions")] == [c.id]
    assert [r.id for r in _list(workflow_id=download.id, status="requested")] == [a.id]
    assert _list(workflow_id="no-such-workflow") == []


def test_list_limit_and_offset(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    workflow = _workflow()
    rows = [_execute(workflow.id) for _ in range(5)]
    newest_first = [r.id for r in reversed(rows)]
    assert [r.id for r in _list(limit=2)] == newest_first[:2]
    assert [r.id for r in _list(limit=2, offset=2)] == newest_first[2:4]
    assert [r.id for r in _list(offset=4)] == newest_first[4:]


def test_create_reads_the_workflow_inside_the_same_shared_transaction(data_dir):
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    new_workflow = AppWfCtx(
        transaction=rolled_back,
        req=AppWfReq(workflow_name="inside", engine_type="apache_airflow", engine_workflow_id="d"),
    )
    assert workflows.create(new_workflow) == SUCCESS  # not committed yet: only this transaction sees it
    execution = AppWfExecLogCtx(transaction=rolled_back, req=AppWfExecLogReq(workflow_id=new_workflow.resp.records[0].id))
    assert logs.create(execution) == SUCCESS
    assert execution.resp.records[0].workflow_name == "inside"
    assert transactions.rollback(rolled_back) == SUCCESS
    assert _list() == []
    assert workflows.get(AppWfCtx(req=AppWfReq(workflow_name="inside"))) == NOT_FOUND

    workflow = _workflow("kept")
    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    kept = AppWfExecLogCtx(transaction=committed, req=AppWfExecLogReq(workflow_id=workflow.id))
    assert logs.create(kept) == SUCCESS
    assert _list() == []  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert [r.id for r in _list()] == [kept.resp.records[0].id]


def test_started_then_failed_is_a_legal_path(data_dir):
    row = _execute(_workflow().id)
    assert _update(row.id, status="started")[0] == SUCCESS
    code, ctx = _update(row.id, status="failed", message="engine reported an error")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert failed.status == "failed" and failed.started_at is not None and failed.finished_at is not None


def test_a_final_row_keeps_its_status_and_times_but_still_accepts_notes(data_dir):
    # D30 protects the status and the times; engine_run_id and message are notes a late callback may still fill in.
    row = _execute(_workflow().id)
    assert _update(row.id, status="started")[0] == SUCCESS
    done = _update(row.id, status="completed")[1].resp.records[0]
    code, ctx = _update(row.id, status="completed", message="late note", engine_run_id="run-9")
    assert code == SUCCESS
    after = ctx.resp.records[0]
    assert (after.status, after.started_at, after.finished_at) == (done.status, done.started_at, done.finished_at)
    assert (after.message, after.engine_run_id) == ("late note", "run-9")


def test_a_rival_move_made_after_the_read_is_not_overwritten(data_dir, monkeypatch):
    # _now() runs after update has read the row and before it writes, so a rival callback that commits inside it
    # is exactly the race: two callbacks both read "started".
    row = _execute(_workflow().id)
    assert _update(row.id, status="started")[0] == SUCCESS
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="failed", message="rival")[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, _ = _update(row.id, status="completed", message="loser")
    assert code == CONFLICT
    stored = _stored(row.id)
    assert (stored.status, stored.message) == ("failed", "rival")  # the loser changed nothing
    assert stored.finished_at is not None


def test_a_rival_that_made_the_same_move_first_is_accepted_like_a_retry(data_dir, monkeypatch):
    row = _execute(_workflow().id)
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="started", engine_run_id="rival-run")[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, ctx = _update(row.id, status="started", message="mine")
    assert code == SUCCESS
    result = ctx.resp.records[0]
    assert (result.status, result.message, result.engine_run_id) == ("started", "mine", "rival-run")
    assert result == _stored(row.id)
    assert result.started_at is not None  # the rival's time, set once


def test_list_rejects_a_negative_limit_or_offset(data_dir):
    _execute(_workflow().id)
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.list(_ctx(limit=-1)) == INVALID_INPUT
    assert logs.list(_ctx(offset=-1)) == INVALID_INPUT
    zero = _ctx(limit=0)
    assert logs.list(zero) == SUCCESS and zero.resp.records == []
