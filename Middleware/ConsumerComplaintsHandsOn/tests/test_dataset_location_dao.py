import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.app_types_constants import DatasetLocationType
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_dataset_location_dao as dao_impl
from app.core.dao.impl.models import DatasetLocationModel
from app.core.dao.objects_factory import DaoObjectsFactory

URL = "https://example.com/file.csv"


def _dataset(name="t_ds", code="T1") -> str:
    ctx = DatasetCtx(req=DatasetReq(name=name, code=code))
    assert DaoObjectsFactory.get_dataset_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ctx(**fields) -> DatasetLocationCtx:
    return DatasetLocationCtx(req=DatasetLocationReq(**fields))


def _create(dao, dataset_id, location_type="http", path=URL, **more) -> DatasetLocationCtx:
    ctx = _ctx(dataset_id=dataset_id, location_type=location_type, path=path, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _add_link(data_dir, location_id):
    """A link written directly: the link DAO comes in a later task."""
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, 'some-mio', 'some-dataset', ?, '2026-01-01 00:00:00')",
            (f"link-{location_id}", location_id),
        )


def test_create_an_http_location_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    row = _create(dao, dataset_id, path="  " + URL + "  ", description="d", credentials_ref="aws_prod.key-1").resp.records[0]
    assert len(row.id) == 36
    assert (row.dataset_id, row.location_type, row.path) == (dataset_id, "http", URL)
    assert (row.local_env_var_name, row.credentials_ref, row.description) == (None, "aws_prod.key-1", "d")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_a_local_location_has_a_path_or_an_env_var_name(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    with_path = _create(dao, dataset_id, location_type="local", path="/data/files").resp.records[0]
    assert (with_path.path, with_path.local_env_var_name) == ("/data/files", None)
    with_env = _create(dao, dataset_id, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1")
    assert (with_env.resp.records[0].path, with_env.resp.records[0].local_env_var_name) == (None, "LOCAL_DATA_PATH_T1")


@pytest.mark.parametrize("location_type", DatasetLocationType.values())
def test_every_location_type_is_accepted_with_a_path(data_dir, location_type):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    row = _create(dao, _dataset(), location_type=location_type, path="somewhere/else").resp.records[0]
    assert row.location_type == location_type


def test_create_rejects_the_wrong_shape(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    other_code = "LOCAL_DATA_PATH_T2"
    bad = [
        dict(location_type="local", path="/a", local_env_var_name="LOCAL_DATA_PATH_T1"),  # both
        dict(location_type="local"),  # neither
        dict(location_type="http", local_env_var_name="LOCAL_DATA_PATH_T1"),  # env var for a type that is not local
        dict(location_type="http"),  # a non-local type needs a path
        dict(location_type="local", local_env_var_name=other_code),  # the name is built from another dataset's code
        dict(location_type="local", local_env_var_name="LOCAL_DATA_PATH_"),
        dict(location_type="local", local_env_var_name="MY_PATH"),
        dict(location_type="dropbox", path="/a"),
        dict(location_type=None, path="/a"),
        dict(location_type="http", path="   "),
        dict(location_type="http", path="p" * 1001),
        dict(location_type="http", path=5),
    ]
    for fields in bad:
        assert dao.create(_ctx(dataset_id=dataset_id, **fields)) == INVALID_INPUT, fields
    assert dao.create(_ctx(location_type="http", path="/a")) == INVALID_INPUT  # no dataset_id
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path="p" * 1000)) == SUCCESS


def test_create_for_a_dataset_that_does_not_exist_is_not_found(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    assert dao.create(_ctx(dataset_id="nope", location_type="http", path=URL)) == NOT_FOUND


@pytest.mark.parametrize("credentials_ref", ["key=abc", "https://host/x", "a b", "", "x" * 101, "AKIA SECRET", "a/b", 5])
def test_a_credentials_reference_that_is_not_a_plain_name_is_rejected(data_dir, credentials_ref):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path=URL, credentials_ref=credentials_ref)) == INVALID_INPUT
    row = _create(dao, dataset_id).resp.records[0]
    assert dao.update(_ctx(id=row.id, credentials_ref=credentials_ref)) == INVALID_INPUT


def test_a_credentials_reference_of_100_characters_is_accepted(data_dir):
    assert _create(DaoObjectsFactory.get_dataset_location_dao(), _dataset(), credentials_ref="x" * 100).resp.records


def test_duplicates_are_conflicts(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    first, second = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    _create(dao, first)
    assert dao.create(_ctx(dataset_id=first, location_type="http", path=URL)) == CONFLICT
    assert dao.create(_ctx(dataset_id=first, location_type="ftp", path=URL)) == SUCCESS  # same path, other type
    assert dao.create(_ctx(dataset_id=second, location_type="http", path=URL)) == SUCCESS  # same path, other dataset
    _create(dao, first, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1")
    again = _ctx(dataset_id=first, location_type="local", local_env_var_name="LOCAL_DATA_PATH_T1")
    assert dao.create(again) == CONFLICT


def test_get_and_list_with_filters_and_a_fixed_order(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    mine, theirs = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    env = _create(dao, mine, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1").resp.records[0]
    ftp = _create(dao, mine, location_type="ftp", path="ftp://h/f").resp.records[0]
    http_b = _create(dao, mine, path="https://b").resp.records[0]
    http_a = _create(dao, mine, path="https://a").resp.records[0]
    _create(dao, theirs, path="https://c")

    everything = _ctx(dataset_id=mine)
    assert dao.list(everything) == SUCCESS
    assert [r.id for r in everything.resp.records] == [ftp.id, http_a.id, http_b.id, env.id]
    only_http = _ctx(dataset_id=mine, location_type="http")
    assert dao.list(only_http) == SUCCESS and [r.id for r in only_http.resp.records] == [http_a.id, http_b.id]
    all_http = _ctx(location_type="http")
    assert dao.list(all_http) == SUCCESS
    assert {r.dataset_id for r in all_http.resp.records} >= {mine, theirs}

    fetched = _ctx(id=ftp.id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].path == "ftp://h/f"
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND


def test_update_changes_the_given_fields_and_path_and_env_var_name_replace_each_other(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    row = _create(dao, dataset_id, location_type="local", path="/data").resp.records[0]

    to_env = _ctx(id=row.id, local_env_var_name="LOCAL_DATA_PATH_T1")
    assert dao.update(to_env) == SUCCESS
    assert (to_env.resp.records[0].path, to_env.resp.records[0].local_env_var_name) == (None, "LOCAL_DATA_PATH_T1")
    assert to_env.resp.records[0].created_at == row.created_at

    to_path = _ctx(id=row.id, path=" /elsewhere ", description="moved", credentials_ref="my_ref")
    assert dao.update(to_path) == SUCCESS
    new = to_path.resp.records[0]
    assert (new.path, new.local_env_var_name, new.description, new.credentials_ref) == ("/elsewhere", None, "moved", "my_ref")

    to_http = _ctx(id=row.id, location_type="http", path=URL)
    assert dao.update(to_http) == SUCCESS and to_http.resp.records[0].location_type == "http"


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id, other_dataset_id = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    local_env = _create(dao, dataset_id, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1").resp.records[0]
    http = _create(dao, dataset_id).resp.records[0]
    _create(dao, dataset_id, path="https://other")

    assert dao.update(_ctx(path="x")) == INVALID_INPUT  # no id
    assert dao.update(_ctx(id="nope", path="x")) == NOT_FOUND
    assert dao.update(_ctx(id=http.id, path="/a", local_env_var_name="LOCAL_DATA_PATH_T1")) == INVALID_INPUT  # both
    assert dao.update(_ctx(id=http.id, local_env_var_name="LOCAL_DATA_PATH_T1")) == INVALID_INPUT  # http cannot have one
    assert dao.update(_ctx(id=local_env.id, location_type="http")) == INVALID_INPUT  # http with no path
    assert dao.update(_ctx(id=local_env.id, local_env_var_name="LOCAL_DATA_PATH_T2")) == INVALID_INPUT  # another dataset's code
    assert dao.update(_ctx(id=http.id, location_type="dropbox")) == INVALID_INPUT
    assert dao.update(_ctx(id=http.id, path="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=http.id, dataset_id=other_dataset_id)) == INVALID_INPUT  # a location cannot move
    assert dao.update(_ctx(id=http.id, path="https://other")) == CONFLICT
    assert dao.update(_ctx(id=http.id, dataset_id=dataset_id, path=URL)) == SUCCESS  # itself is not a conflict
    still = _ctx(id=local_env.id)
    assert dao.get(still) == SUCCESS and still.resp.records[0].local_env_var_name == "LOCAL_DATA_PATH_T1"


def test_delete_returns_the_row_and_a_location_in_use_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    free = _create(dao, dataset_id, path="https://free").resp.records[0]
    used = _create(dao, dataset_id, path="https://used").resp.records[0]
    _add_link(data_dir, used.id)

    deleted = _ctx(id=free.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == free.id
    assert dao.delete(_ctx(id=free.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    assert dao.delete(_ctx(id=used.id)) == CONFLICT
    assert dao.get(_ctx(id=used.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    _create(dao, dataset_id, path="https://taken")
    other = _create(dao, dataset_id, path="https://other").resp.records[0]
    monkeypatch.setattr(dao_impl, "_same_place_query", lambda merged: select(DatasetLocationModel.id).where(false()))
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path="https://taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, path="https://taken")) == CONFLICT
    listed = _ctx(dataset_id=dataset_id)
    assert dao.list(listed) == SUCCESS and sorted(r.path for r in listed.resp.records) == ["https://other", "https://taken"]


def test_a_location_can_join_the_transaction_that_creates_its_dataset(data_dir):
    datasets = DaoObjectsFactory.get_dataset_dao()
    dao = DaoObjectsFactory.get_dataset_location_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    made = DatasetCtx(transaction=tx, req=DatasetReq(name="t_tx", code="T1"))
    assert datasets.create(made) == SUCCESS
    new = DatasetLocationCtx(
        transaction=tx,
        req=DatasetLocationReq(dataset_id=made.resp.records[0].id, location_type="http", path=URL),
    )
    assert dao.create(new) == SUCCESS  # it sees the dataset that is not committed yet
    assert transactions.rollback(tx) == SUCCESS
    assert datasets.get(DatasetCtx(req=DatasetReq(name="t_tx"))) == NOT_FOUND
    assert dao.get(_ctx(id=new.resp.records[0].id)) == NOT_FOUND
