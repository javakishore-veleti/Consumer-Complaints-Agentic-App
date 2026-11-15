import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_dao as dao_impl
from app.core.dao.impl.models import MioModel
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> MioCtx:
    return MioCtx(req=MioReq(**fields))


def _create(dao, name="t_one", **more) -> MioCtx:
    ctx = _ctx(name=name, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _add_link(data_dir, mio_id):
    """A link written directly: the link DAO comes in a later task."""
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, ?, 'some-dataset', 'some-location', '2026-01-01 00:00:00')",
            (f"link-{mio_id}", mio_id),
        )


def _mine(dao) -> list:
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    return [r.name for r in listed.resp.records if r.name.lower().startswith("t_")]


def test_create_returns_the_row(data_dir):
    row = _create(DaoObjectsFactory.get_mio_dao(), name="  t_one  ", description="about").resp.records[0]
    assert len(row.id) == 36
    assert (row.name, row.description) == ("t_one", "about")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_create_accepts_a_100_character_name(data_dir):
    assert len(_create(DaoObjectsFactory.get_mio_dao(), name="n" * 100).resp.records[0].name) == 100


@pytest.mark.parametrize("name", [None, "", "   ", "n" * 101, 5])
def test_create_rejects_a_missing_or_unacceptable_name(data_dir, name):
    assert DaoObjectsFactory.get_mio_dao().create(_ctx(name=name)) == INVALID_INPUT


def test_names_are_trimmed_and_case_sensitive(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_one")
    assert dao.create(_ctx(name=" t_one ")) == CONFLICT
    assert dao.create(_ctx(name="T_ONE")) == SUCCESS
    assert sorted(_mine(dao)) == ["T_ONE", "t_one"]


def test_get_by_id_or_by_name_and_the_id_wins(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    one = _create(dao, name="t_one").resp.records[0]
    two = _create(dao, name="t_two").resp.records[0]
    by_id, by_name, both = _ctx(id=one.id), _ctx(name=" t_two "), _ctx(id=one.id, name="t_two")
    assert dao.get(by_id) == SUCCESS and by_id.resp.records[0].id == one.id
    assert dao.get(by_name) == SUCCESS and by_name.resp.records[0].id == two.id
    assert dao.get(both) == SUCCESS and both.resp.records[0].id == one.id
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(name=5)) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx(name="nope")) == NOT_FOUND


def test_list_is_ordered_by_name_and_includes_the_seeded_mios(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_b")
    _create(dao, name="t_a")
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    names = [r.name for r in listed.resp.records]
    assert names == sorted(names)
    assert sum(name.startswith("Customer complaints ") for name in names) == 5
    assert _mine(dao) == ["t_a", "t_b"]


def test_update_changes_only_the_given_fields(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao, description="before").resp.records[0]
    described = _ctx(id=row.id, description="after")
    assert dao.update(described) == SUCCESS
    assert (described.resp.records[0].name, described.resp.records[0].description) == ("t_one", "after")
    assert described.resp.records[0].created_at == row.created_at
    renamed = _ctx(id=row.id, name="  t_renamed ")
    assert dao.update(renamed) == SUCCESS and renamed.resp.records[0].name == "t_renamed"
    assert renamed.resp.records[0].description == "after"
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS  # its own name is not a conflict


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    one = _create(dao, name="t_one").resp.records[0]
    _create(dao, name="t_two")
    assert dao.update(_ctx(name="x")) == INVALID_INPUT
    assert dao.update(_ctx(id="nope", name="x")) == NOT_FOUND
    assert dao.update(_ctx(id=one.id, name="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="n" * 101)) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name=5)) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="t_two")) == CONFLICT


def test_delete_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao).resp.records[0]
    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT


def test_a_mio_with_a_link_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao).resp.records[0]
    _add_link(data_dir, row.id)
    assert dao.delete(_ctx(id=row.id)) == CONFLICT
    assert dao.get(_ctx(id=row.id)) == SUCCESS
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute("delete from mios_datasets where mio_id = ?", (row.id,))
    assert dao.delete(_ctx(id=row.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_taken")
    other = _create(dao, name="t_other").resp.records[0]
    monkeypatch.setattr(dao_impl, "_taken_query", lambda req: select(MioModel.id).where(false()))
    assert dao.create(_ctx(name="t_taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, name="t_taken")) == CONFLICT
    assert sorted(_mine(dao)) == ["t_other", "t_taken"]


def test_a_shared_transaction_can_be_rolled_back_or_committed(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    assert dao.create(MioCtx(transaction=rolled_back, req=MioReq(name="t_gone"))) == SUCCESS
    assert dao.get(MioCtx(transaction=rolled_back, req=MioReq(name="t_gone"))) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert dao.get(_ctx(name="t_gone")) == NOT_FOUND

    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    assert dao.create(MioCtx(transaction=committed, req=MioReq(name="t_kept"))) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == NOT_FOUND
    assert transactions.commit(committed) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == SUCCESS
