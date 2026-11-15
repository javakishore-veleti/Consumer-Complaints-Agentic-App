"""MioWorkflowDao: bind workflows to MIOs (D84)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

DOWNLOAD_WF = "download_cfpb_all"
FILTER_WF = "filter_cfpb_3_months"


def _mio(name="t_mio") -> str:
    ctx = MioCtx(req=MioReq(name=name))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _wf(name: str) -> str:
    ctx = AppWfCtx(req=AppWfReq(workflow_name=name))
    assert DaoObjectsFactory.get_app_wf_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ctx(**fields) -> MioWorkflowCtx:
    return MioWorkflowCtx(req=MioWorkflowReq(**fields))


def _bind(dao, mio_id, workflow_id) -> MioWorkflowCtx:
    ctx = _ctx(mio_id=mio_id, workflow_id=workflow_id)
    assert dao.create(ctx) == SUCCESS
    return ctx


def test_create_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    mio_id, wf_id = _mio(), _wf(DOWNLOAD_WF)
    row = _bind(dao, mio_id, wf_id).resp.records[0]
    assert len(row.id) == 36
    assert (row.mio_id, row.workflow_id) == (mio_id, wf_id)
    assert row.created_at.tzinfo is not None


def test_create_needs_mio_and_workflow(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    mio_id, wf_id = _mio(), _wf(DOWNLOAD_WF)
    assert dao.create(_ctx(workflow_id=wf_id)) == INVALID_INPUT
    assert dao.create(_ctx(mio_id=mio_id)) == INVALID_INPUT


def test_parents_must_exist(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    mio_id, wf_id = _mio(), _wf(DOWNLOAD_WF)
    assert dao.create(_ctx(mio_id="nope", workflow_id=wf_id)) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, workflow_id="nope")) == NOT_FOUND


def test_unique_mio_workflow_but_many_mios_can_share_a_workflow(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    first, second = _mio("t_a"), _mio("t_b")
    download, filt = _wf(DOWNLOAD_WF), _wf(FILTER_WF)
    _bind(dao, first, download)
    assert dao.create(_ctx(mio_id=first, workflow_id=download)) == CONFLICT
    _bind(dao, second, download)
    _bind(dao, first, filt)


def test_get_and_list_by_mio(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    first, second = _mio("t_a"), _mio("t_b")
    download, filt = _wf(DOWNLOAD_WF), _wf(FILTER_WF)
    one = _bind(dao, first, download).resp.records[0]
    two = _bind(dao, first, filt).resp.records[0]
    three = _bind(dao, second, download).resp.records[0]

    by_mio = _ctx(mio_id=first)
    assert dao.list(by_mio) == SUCCESS
    assert [r.id for r in by_mio.resp.records] == [one.id, two.id]

    by_wf = _ctx(workflow_id=download)
    assert dao.list(by_wf) == SUCCESS
    mine = {one.id, three.id}
    assert mine <= {r.id for r in by_wf.resp.records}

    fetched = _ctx(id=two.id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].workflow_id == filt
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND


def test_delete_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    mio_id, wf_id = _mio(), _wf(DOWNLOAD_WF)
    row = _bind(dao, mio_id, wf_id).resp.records[0]
    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS
    assert deleted.resp.records[0].id == row.id
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    assert dao.delete(_ctx(id="nope")) == NOT_FOUND


def test_seeded_all_and_3_months_bindings_are_readable(data_dir):
    dao = DaoObjectsFactory.get_mio_workflow_dao()
    all_mio = MioCtx(req=MioReq(name="Customer complaints all 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(all_mio) == SUCCESS
    three = MioCtx(req=MioReq(name="Customer complaints 3 months 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(three) == SUCCESS
    all_links = _ctx(mio_id=all_mio.resp.records[0].id)
    three_links = _ctx(mio_id=three.resp.records[0].id)
    assert dao.list(all_links) == SUCCESS
    assert dao.list(three_links) == SUCCESS
    assert [r.workflow_id for r in all_links.resp.records] == [_wf(DOWNLOAD_WF)]
    assert [r.workflow_id for r in three_links.resp.records] == [_wf(FILTER_WF)]
