import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_dataset_dao as dao_impl
from app.core.dao.impl.models import DatasetModel
from app.core.dao.objects_factory import DaoObjectsFactory

STAMP = "2026-01-01 00:00:00"


def _ctx(**fields) -> DatasetCtx:
    return DatasetCtx(req=DatasetReq(**fields))


def _create(dao, name="t_one", code="T1", **more) -> DatasetCtx:
    ctx = _ctx(name=name, code=code, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _admin_db(data_dir):
    return sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite")


def _add_location(data_dir, dataset_id, path=None, env_var=None):
    """A child row written directly: the location DAO comes in a later task."""
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into datasets_location (id, dataset_id, location_type, path, local_env_var_name, created_at,"
            " updated_at) values (?, ?, ?, ?, ?, ?, ?)",
            (f"loc-{dataset_id}-{env_var or path}", dataset_id, "local" if env_var else "http", path, env_var, STAMP, STAMP),
        )


def _add_link(data_dir, dataset_id):
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, 'some-mio', ?, 'some-location', ?)",
            (f"link-{dataset_id}", dataset_id, STAMP),
        )


def _mine(dao) -> list:
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    return [r.name for r in listed.resp.records if r.name.lower().startswith("t_")]


def test_create_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao, name="  t_one  ", description="about").resp.records[0]
    assert len(row.id) == 36
    assert (row.name, row.code, row.description) == ("t_one", "T1", "about")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_create_accepts_the_longest_name_and_code(data_dir):
    row = _create(DaoObjectsFactory.get_dataset_dao(), name="n" * 100, code="A" * 14 + "9").resp.records[0]
    assert len(row.name) == 100 and len(row.code) == 15


@pytest.mark.parametrize(
    "fields",
    [
        dict(name=None, code="T1"),
        dict(name="   ", code="T1"),
        dict(name="n" * 101, code="T1"),
        dict(name="t_x", code=None),
        dict(name="t_x", code=""),
        dict(name="t_x", code="abc"),
        dict(name="t_x", code="A B"),
        dict(name="t_x", code="A_B"),
        dict(name="t_x", code="A" * 16),
        dict(name="t_x", code=5),
    ],
)
def test_create_rejects_bad_input(data_dir, fields):
    assert DaoObjectsFactory.get_dataset_dao().create(_ctx(**fields)) == INVALID_INPUT


def test_a_name_or_a_code_that_is_taken_is_a_conflict_and_names_are_trimmed_and_case_sensitive(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_one", code="T1")
    assert dao.create(_ctx(name=" t_one ", code="T2")) == CONFLICT
    assert dao.create(_ctx(name="t_two", code="T1")) == CONFLICT
    assert dao.create(_ctx(name="T_ONE", code="T3")) == SUCCESS  # a different case is a different name
    assert sorted(_mine(dao)) == ["T_ONE", "t_one"]


def test_get_by_id_or_by_name_and_the_id_wins(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    one = _create(dao, name="t_one", code="T1").resp.records[0]
    two = _create(dao, name="t_two", code="T2").resp.records[0]
    by_id, by_name, both = _ctx(id=one.id), _ctx(name=" t_two "), _ctx(id=one.id, name="t_two")
    assert dao.get(by_id) == SUCCESS and by_id.resp.records[0].id == one.id
    assert dao.get(by_name) == SUCCESS and by_name.resp.records[0].id == two.id
    assert dao.get(both) == SUCCESS and both.resp.records[0].id == one.id
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx(name="nope")) == NOT_FOUND


def test_list_is_ordered_by_name_and_includes_the_seed(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_b", code="T2")
    _create(dao, name="t_a", code="T1")
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    names = [r.name for r in listed.resp.records]
    assert names == sorted(names)
    assert "cfpb_consumer_complaints" in names
    assert _mine(dao) == ["t_a", "t_b"]


def test_update_changes_only_the_given_fields(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao, description="before").resp.records[0]
    described = _ctx(id=row.id, description="after")
    assert dao.update(described) == SUCCESS
    new = described.resp.records[0]
    assert (new.name, new.code, new.description) == ("t_one", "T1", "after")
    assert new.created_at == row.created_at and new.updated_at >= row.updated_at
    renamed = _ctx(id=row.id, name="  t_renamed ", code="T2")
    assert dao.update(renamed) == SUCCESS
    assert (renamed.resp.records[0].name, renamed.resp.records[0].code) == ("t_renamed", "T2")
    assert renamed.resp.records[0].description == "after"
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS  # its own name is not a conflict


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    one = _create(dao, name="t_one", code="T1").resp.records[0]
    _create(dao, name="t_two", code="T2")
    assert dao.update(_ctx(name="x")) == INVALID_INPUT
    assert dao.update(_ctx(id="nope", name="x")) == NOT_FOUND
    assert dao.update(_ctx(id=one.id, name="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, code="abc")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="t_two")) == CONFLICT
    assert dao.update(_ctx(id=one.id, code="T2")) == CONFLICT


def test_the_code_cannot_change_while_a_location_holds_an_env_var_name_built_from_it(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao).resp.records[0]
    _add_location(data_dir, row.id, env_var="LOCAL_DATA_PATH_T1")
    assert dao.update(_ctx(id=row.id, code="T2")) == CONFLICT
    assert dao.update(_ctx(id=row.id, code="T1")) == SUCCESS  # the same code is not a change
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS
    plain = _create(dao, name="t_plain", code="T3").resp.records[0]
    _add_location(data_dir, plain.id, path="https://example.com/file")  # a path needs no code
    assert dao.update(_ctx(id=plain.id, code="T4")) == SUCCESS


def test_delete_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao).resp.records[0]
    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT


def test_a_dataset_in_use_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    with_location = _create(dao, name="t_loc", code="T1").resp.records[0]
    with_link = _create(dao, name="t_link", code="T2").resp.records[0]
    _add_location(data_dir, with_location.id, path="https://example.com/file")
    _add_link(data_dir, with_link.id)
    assert dao.delete(_ctx(id=with_location.id)) == CONFLICT
    assert dao.delete(_ctx(id=with_link.id)) == CONFLICT
    assert _mine(dao) == ["t_link", "t_loc"]
    with _admin_db(data_dir) as db:
        db.execute("delete from datasets_location where dataset_id = ?", (with_location.id,))
        db.execute("delete from mios_datasets where dataset_id = ?", (with_link.id,))
    assert dao.delete(_ctx(id=with_location.id)) == SUCCESS
    assert dao.delete(_ctx(id=with_link.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    # Simulates the race: another writer inserts the same name or code after our SELECT, so only the constraint catches it.
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_taken", code="T1")
    other = _create(dao, name="t_other", code="T2").resp.records[0]
    monkeypatch.setattr(dao_impl, "_taken_query", lambda req: select(DatasetModel.id).where(false()))
    assert dao.create(_ctx(name="t_taken", code="T9")) == CONFLICT
    assert dao.create(_ctx(name="t_new", code="T1")) == CONFLICT
    assert dao.update(_ctx(id=other.id, name="t_taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, code="T1")) == CONFLICT
    assert _mine(dao) == ["t_other", "t_taken"]


def test_a_shared_transaction_can_be_rolled_back_or_committed(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    gone = DatasetCtx(transaction=rolled_back, req=DatasetReq(name="t_gone", code="T1"))
    assert dao.create(gone) == SUCCESS
    assert dao.get(DatasetCtx(transaction=rolled_back, req=DatasetReq(name="t_gone"))) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert dao.get(_ctx(name="t_gone")) == NOT_FOUND

    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    assert dao.create(DatasetCtx(transaction=committed, req=DatasetReq(name="t_kept", code="T2"))) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == NOT_FOUND  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == SUCCESS
