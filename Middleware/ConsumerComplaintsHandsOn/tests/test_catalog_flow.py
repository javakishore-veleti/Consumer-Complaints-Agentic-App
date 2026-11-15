from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowReq
from app.core.common.return_codes import CONFLICT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SEED_MIO_NAMES = ["Customer complaints all 2026"] + [
    f"Customer complaints {months} months 2026" for months in (3, 6, 9, 12)
]


def _seed_dataset():
    ctx = DatasetCtx(req=DatasetReq(name="cfpb_consumer_complaints"))
    assert DaoObjectsFactory.get_dataset_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def _links_of(mio_id):
    ctx = MioDatasetCtx(req=MioDatasetReq(mio_id=mio_id))
    assert DaoObjectsFactory.get_mio_dataset_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def _workflow_links_of(mio_id):
    ctx = MioWorkflowCtx(req=MioWorkflowReq(mio_id=mio_id))
    assert DaoObjectsFactory.get_mio_workflow_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def test_the_seed_can_be_read_through_the_daos(data_dir):
    dataset = _seed_dataset()
    assert dataset.code == "CFPB"

    places = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert DaoObjectsFactory.get_dataset_location_dao().list(places) == SUCCESS
    by_type = {p.location_type: p for p in places.resp.records}
    assert sorted(by_type) == ["http", "local"]
    assert by_type["http"].path == "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
    assert by_type["http"].credentials_ref is None
    assert (by_type["local"].path, by_type["local"].local_env_var_name) == (None, "LOCAL_DATA_PATH_CFPB")

    for name in SEED_MIO_NAMES:
        mio = MioCtx(req=MioReq(name=name))
        assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
        links = _links_of(mio.resp.records[0].id)
        assert [(link.dataset_id, link.dataset_location_id) for link in links] == [(dataset.id, by_type["http"].id)]


def test_a_mio_name_decides_nothing_about_its_data(data_dir):
    dataset = _seed_dataset()
    mios = DaoObjectsFactory.get_mio_dao()
    before = MioCtx(req=MioReq(name="Customer complaints 3 months 2026"))
    assert mios.get(before) == SUCCESS
    mio_id = before.resp.records[0].id
    links_before = [(link.dataset_id, link.dataset_location_id) for link in _links_of(mio_id)]

    renamed = MioCtx(req=MioReq(id=mio_id, name="Something unrelated", description="no window here"))
    assert mios.update(renamed) == SUCCESS
    assert [(link.dataset_id, link.dataset_location_id) for link in _links_of(mio_id)] == links_before

    # A new MIO with any name reuses the same dataset and the same location.
    http_id = links_before[0][1]
    fresh = MioCtx(req=MioReq(name="Customer complaints 100 years"))
    assert mios.create(fresh) == SUCCESS
    link = MioDatasetCtx(
        req=MioDatasetReq(mio_id=fresh.resp.records[0].id, dataset_id=dataset.id, dataset_location_id=http_id)
    )
    assert DaoObjectsFactory.get_mio_dataset_dao().create(link) == SUCCESS


def test_the_catalog_is_taken_apart_from_the_links_to_the_dataset(data_dir):
    datasets = DaoObjectsFactory.get_dataset_dao()
    locations = DaoObjectsFactory.get_dataset_location_dao()
    mios = DaoObjectsFactory.get_mio_dao()
    links = DaoObjectsFactory.get_mio_dataset_dao()
    wf_links = DaoObjectsFactory.get_mio_workflow_dao()
    dataset = _seed_dataset()
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == CONFLICT  # locations and links use it

    for name in SEED_MIO_NAMES:
        mio = MioCtx(req=MioReq(name=name))
        assert mios.get(mio) == SUCCESS
        mio_id = mio.resp.records[0].id
        assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == CONFLICT  # its link is still there
        for link in _links_of(mio_id):
            assert links.delete(MioDatasetCtx(req=MioDatasetReq(id=link.id))) == SUCCESS
        for link in _workflow_links_of(mio_id):
            assert wf_links.delete(MioWorkflowCtx(req=MioWorkflowReq(id=link.id))) == SUCCESS
        assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == SUCCESS

    places = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert locations.list(places) == SUCCESS
    for place in places.resp.records:
        assert locations.delete(DatasetLocationCtx(req=DatasetLocationReq(id=place.id))) == SUCCESS
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == SUCCESS
