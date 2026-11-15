"""Every MIO with the status of its latest ingest and that ingest's executions (D61)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_NAMES = [
    "Customer complaints 12 months 2026",
    "Customer complaints 3 months 2026",
    "Customer complaints 6 months 2026",
    "Customer complaints 9 months 2026",
    "Customer complaints all 2026",
]
SEEDED_3M = "Customer complaints 3 months 2026"


def _read(req: MioStatusReq | None = None) -> MioStatusCtx:
    ctx = MioStatusCtx(req=req or MioStatusReq())
    ServicesObjectsFactory.get_mio_status_service().read(ctx)
    return ctx


@pytest.fixture
def workflow_id(data_dir):
    ctx = AppWfCtx(req=AppWfReq(workflow_name="t_status", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def seeded_3m_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_3M))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    return mio.resp.records[0].id


def test_every_seeded_mio_appears_ordered_by_name_with_no_ingest(data_dir):
    ctx = _read()
    assert ctx.resp.code == SUCCESS
    assert [e.name for e in ctx.resp.entries] == SEEDED_NAMES
    assert all(e.latest_ingest is None for e in ctx.resp.entries)


def test_latest_ingest_and_its_executions_are_nested(seeded_3m_id, workflow_id):
    older = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="old"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(older) == SUCCESS
    newer = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="new"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(newer) == SUCCESS
    newer_id = newer.resp.records[0].id
    first = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=newer_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(first) == SUCCESS
    second = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=newer_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(second) == SUCCESS

    ctx = _read()
    assert ctx.resp.code == SUCCESS
    entry = next(e for e in ctx.resp.entries if e.id == seeded_3m_id)
    assert entry.latest_ingest is not None
    assert (entry.latest_ingest.id, entry.latest_ingest.message) == (newer_id, "new")
    assert [x.id for x in entry.latest_ingest.executions] == [second.resp.records[0].id, first.resp.records[0].id]
    others = [e for e in ctx.resp.entries if e.id != seeded_3m_id]
    assert all(e.latest_ingest is None for e in others)


def test_an_ingest_without_executions_has_an_empty_list(seeded_3m_id):
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    ctx = _read(MioStatusReq(mio_id=seeded_3m_id))
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].latest_ingest.executions == []


def test_mio_id_returns_one_entry(seeded_3m_id):
    ctx = _read(MioStatusReq(mio_id=seeded_3m_id))
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].id == seeded_3m_id
    assert ctx.resp.entries[0].latest_ingest is None


def test_unknown_mio_id_is_not_found(data_dir):
    assert _read(MioStatusReq(mio_id="no-such-mio")).resp.code == NOT_FOUND


@pytest.mark.parametrize("mio_id", ["", "   "])
def test_blank_mio_id_is_invalid(data_dir, mio_id):
    assert _read(MioStatusReq(mio_id=mio_id)).resp.code == INVALID_INPUT


def test_the_facade_hands_the_read_on(seeded_3m_id):
    ctx = MioStatusFacadeCtx(req=MioStatusReq(mio_id=seeded_3m_id))
    assert FacadesObjectsFactory.get_mio_status_facade().read(ctx) == SUCCESS
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].id == seeded_3m_id
