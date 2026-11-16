"""MioAclDao (D89)."""

from app.core.common.dtos.mio_acl_dtos import MioAclCtx, MioAclReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

ALL_MIO = "Customer complaints all 2026"


def test_create_list_seeded_and_delete(data_dir):
    dao = DaoObjectsFactory.get_mio_acl_dao()
    mio = MioCtx(req=MioReq(name=ALL_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    listed = MioAclCtx(req=MioAclReq(mio_id=mio_id, audience="internal"))
    assert dao.list(listed) == SUCCESS
    assert listed.resp.records and listed.resp.records[0].audience == "internal"

    made = MioCtx(req=MioReq(name="t_acl_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(made) == SUCCESS
    new_id = made.resp.records[0].id
    created = MioAclCtx(req=MioAclReq(mio_id=new_id, audience="partner"))
    assert dao.create(created) == SUCCESS
    assert dao.create(MioAclCtx(req=MioAclReq(mio_id=new_id, audience="partner"))) == CONFLICT
    assert dao.create(MioAclCtx(req=MioAclReq(mio_id=new_id, audience="bogus"))) == INVALID_INPUT
    assert dao.create(MioAclCtx(req=MioAclReq(mio_id="missing", audience="user"))) == NOT_FOUND

    row_id = created.resp.records[0].id
    deleted = MioAclCtx(req=MioAclReq(id=row_id))
    assert dao.delete(deleted) == SUCCESS
    assert dao.delete(MioAclCtx(req=MioAclReq(id=row_id))) == NOT_FOUND
