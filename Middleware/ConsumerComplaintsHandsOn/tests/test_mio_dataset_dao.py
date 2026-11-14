from sqlalchemy import false, select

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_dataset_dao as dao_impl
from app.core.dao.impl.models import MioDatasetModel
from app.core.dao.objects_factory import DaoObjectsFactory


def _dataset(name="t_ds", code="T1") -> str:
    ctx = DatasetCtx(req=DatasetReq(name=name, code=code))
    assert DaoObjectsFactory.get_dataset_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _location(dataset_id, path="https://example.com/a") -> str:
    ctx = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset_id, location_type="http", path=path))
    assert DaoObjectsFactory.get_dataset_location_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _mio(name="t_mio") -> str:
    ctx = MioCtx(req=MioReq(name=name))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ctx(**fields) -> MioDatasetCtx:
    return MioDatasetCtx(req=MioDatasetReq(**fields))


def _link(dao, mio_id, dataset_id, location_id) -> MioDatasetCtx:
    ctx = _ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=location_id)
    assert dao.create(ctx) == SUCCESS
    return ctx


def test_create_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    row = _link(dao, mio_id, dataset_id, location_id).resp.records[0]
    assert len(row.id) == 36
    assert (row.mio_id, row.dataset_id, row.dataset_location_id) == (mio_id, dataset_id, location_id)
    assert row.created_at.tzinfo is not None


def test_create_needs_all_three_ids(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    assert dao.create(_ctx(dataset_id=dataset_id, dataset_location_id=location_id)) == INVALID_INPUT
    assert dao.create(_ctx(mio_id=mio_id, dataset_location_id=location_id)) == INVALID_INPUT
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id)) == INVALID_INPUT


def test_every_parent_must_exist_and_the_location_must_belong_to_the_dataset(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id, other_dataset_id = _mio(), _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    location_id, other_location_id = _location(dataset_id), _location(other_dataset_id)
    assert dao.create(_ctx(mio_id="nope", dataset_id=dataset_id, dataset_location_id=location_id)) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id="nope", dataset_location_id=location_id)) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id="nope")) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=other_location_id)) == INVALID_INPUT


def test_a_mio_has_one_link_per_dataset_but_many_mios_can_share_a_dataset_and_a_location(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    first, second = _mio("t_first"), _mio("t_second")
    dataset_id, other_dataset_id = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    location_id, other_location_id = _location(dataset_id), _location(other_dataset_id)
    _link(dao, first, dataset_id, location_id)
    assert dao.create(_ctx(mio_id=first, dataset_id=dataset_id, dataset_location_id=location_id)) == CONFLICT
    _link(dao, second, dataset_id, location_id)  # another MIO may use the same dataset and the same location
    _link(dao, first, other_dataset_id, other_location_id)  # one MIO may use another dataset


def test_get_and_list_with_filters_in_creation_order(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    first, second = _mio("t_first"), _mio("t_second")
    a, b = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    loc_a, loc_b = _location(a), _location(b)
    one = _link(dao, first, a, loc_a).resp.records[0]
    two = _link(dao, first, b, loc_b).resp.records[0]
    three = _link(dao, second, a, loc_a).resp.records[0]

    by_mio = _ctx(mio_id=first)
    assert dao.list(by_mio) == SUCCESS and [r.id for r in by_mio.resp.records] == [one.id, two.id]
    by_dataset = _ctx(dataset_id=a)
    assert dao.list(by_dataset) == SUCCESS and [r.id for r in by_dataset.resp.records] == [one.id, three.id]
    both = _ctx(mio_id=second, dataset_id=a)
    assert dao.list(both) == SUCCESS and [r.id for r in both.resp.records] == [three.id]

    fetched = _ctx(id=two.id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].dataset_location_id == loc_b
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND


def test_update_may_only_change_the_chosen_location_to_another_location_of_the_same_dataset(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id, other_dataset_id = _mio(), _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    http, mirror = _location(dataset_id), _location(dataset_id, path="https://mirror.example.com/a")
    foreign = _location(other_dataset_id)
    row = _link(dao, mio_id, dataset_id, http).resp.records[0]

    moved = _ctx(id=row.id, dataset_location_id=mirror)
    assert dao.update(moved) == SUCCESS
    assert (moved.resp.records[0].dataset_location_id, moved.resp.records[0].created_at) == (mirror, row.created_at)
    assert dao.update(_ctx(id=row.id, dataset_location_id=foreign)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, dataset_location_id="nope")) == NOT_FOUND
    assert dao.update(_ctx(id=row.id)) == INVALID_INPUT  # nothing to change
    assert dao.update(_ctx(dataset_location_id=http)) == INVALID_INPUT  # no id
    assert dao.update(_ctx(id="nope", dataset_location_id=http)) == NOT_FOUND
    assert dao.update(_ctx(id=row.id, mio_id="another", dataset_location_id=http)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, dataset_id=other_dataset_id, dataset_location_id=http)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=http)) == SUCCESS


def test_delete_returns_the_row_and_frees_the_parents(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    row = _link(dao, mio_id, dataset_id, location_id).resp.records[0]
    assert DaoObjectsFactory.get_mio_dao().delete(MioCtx(req=MioReq(id=mio_id))) == CONFLICT
    assert DaoObjectsFactory.get_dataset_location_dao().delete(DatasetLocationCtx(req=DatasetLocationReq(id=location_id))) == CONFLICT

    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    assert DaoObjectsFactory.get_mio_dao().delete(MioCtx(req=MioReq(id=mio_id))) == SUCCESS
    assert DaoObjectsFactory.get_dataset_location_dao().delete(DatasetLocationCtx(req=DatasetLocationReq(id=location_id))) == SUCCESS
    assert DaoObjectsFactory.get_dataset_dao().delete(DatasetCtx(req=DatasetReq(id=dataset_id))) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    _link(dao, mio_id, dataset_id, location_id)
    monkeypatch.setattr(dao_impl, "_same_link_query", lambda req: select(MioDatasetModel.id).where(false()))
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=location_id)) == CONFLICT
    listed = _ctx(mio_id=mio_id)
    assert dao.list(listed) == SUCCESS and len(listed.resp.records) == 1


def test_a_link_can_join_the_transaction_that_creates_its_parents(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()
    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    mio = MioCtx(transaction=tx, req=MioReq(name="t_tx"))
    dataset = DatasetCtx(transaction=tx, req=DatasetReq(name="t_tx_ds", code="T1"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    assert DaoObjectsFactory.get_dataset_dao().create(dataset) == SUCCESS
    place = DatasetLocationCtx(
        transaction=tx,
        req=DatasetLocationReq(dataset_id=dataset.resp.records[0].id, location_type="http", path="https://x"),
    )
    assert DaoObjectsFactory.get_dataset_location_dao().create(place) == SUCCESS
    link = MioDatasetCtx(
        transaction=tx,
        req=MioDatasetReq(
            mio_id=mio.resp.records[0].id,
            dataset_id=dataset.resp.records[0].id,
            dataset_location_id=place.resp.records[0].id,
        ),
    )
    assert dao.create(link) == SUCCESS
    assert transactions.rollback(tx) == SUCCESS
    assert dao.get(_ctx(id=link.resp.records[0].id)) == NOT_FOUND
    assert DaoObjectsFactory.get_mio_dao().get(MioCtx(req=MioReq(name="t_tx"))) == NOT_FOUND
