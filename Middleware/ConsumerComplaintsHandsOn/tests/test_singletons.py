from concurrent.futures import ThreadPoolExecutor

from app.api.objects_factory import ApiObjectsFactory
from app.api.routers.data_ingest_api import DataIngestApi
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao
from app.core.dao.impl.sqlalchemy_data_ingest_dao import SqlAlchemyDataIngestDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl
from app.core.facades.impl.tasks.data_ingest_call_dao_task import DataIngestCallDaoTask
from app.core.facades.impl.tasks.data_ingest_collect_response_task import DataIngestCollectResponseTask
from app.core.facades.impl.tasks.data_ingest_prepare_dao_ctx_task import DataIngestPrepareDaoCtxTask
from app.core.facades.impl.tasks.data_ingest_validate_request_task import DataIngestValidateRequestTask
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory
from app.core.dao.impl.sqlalchemy_system_datasets_dao import SqlAlchemySystemDatasetsDao
from app.core.dao.impl.sqlalchemy_transaction_dao import SqlAlchemyTransactionDao
from app.core.dao.system_datasets_dao import SystemDatasetsDao
from app.core.dao.transaction_dao import TransactionDao


def test_factories_return_the_same_object_typed_as_the_interface():
    dao = DaoObjectsFactory.get_data_ingest_dao()
    assert dao is DaoObjectsFactory.get_data_ingest_dao()
    assert isinstance(dao, DataIngestDao)

    facade = FacadesObjectsFactory.get_data_ingest_facade()
    assert facade is FacadesObjectsFactory.get_data_ingest_facade()
    assert isinstance(facade, DataIngestFacade)

    for getter, interface in (
        (DaoObjectsFactory.get_app_wf_dao, AppWfDao),
        (DaoObjectsFactory.get_system_datasets_dao, SystemDatasetsDao),
        (DaoObjectsFactory.get_transaction_dao, TransactionDao),
        (ServicesObjectsFactory.get_dataset_status_service, DatasetStatusService),
    ):
        assert getter() is getter()
        assert isinstance(getter(), interface)

    assert ApiObjectsFactory.get_app() is ApiObjectsFactory.get_app()


def test_the_classes_themselves_are_singletons():
    assert SqlAlchemyDataIngestDao() is SqlAlchemyDataIngestDao()
    assert SqlAlchemyAppWfDao() is SqlAlchemyAppWfDao()
    assert DataIngestApi() is DataIngestApi()
    assert DataIngestFacadeImpl() is DataIngestFacadeImpl()
    assert SqlAlchemySystemDatasetsDao() is SqlAlchemySystemDatasetsDao()
    assert SqlAlchemyTransactionDao() is SqlAlchemyTransactionDao()
    assert DatasetStatusServiceImpl() is DatasetStatusServiceImpl()
    for task in (
        DataIngestValidateRequestTask,
        DataIngestPrepareDaoCtxTask,
        DataIngestCallDaoTask,
        DataIngestCollectResponseTask,
    ):
        assert task() is task()


def test_one_object_even_when_many_threads_ask_at_once():
    with ThreadPoolExecutor(max_workers=16) as pool:
        daos = list(pool.map(lambda _: DaoObjectsFactory.get_data_ingest_dao(), range(200)))
        facades = list(pool.map(lambda _: FacadesObjectsFactory.get_data_ingest_facade(), range(200)))
    assert len({id(d) for d in daos}) == 1
    assert len({id(f) for f in facades}) == 1
