from concurrent.futures import ThreadPoolExecutor

from app.api.objects_factory import ApiObjectsFactory
from app.api.routers.airflow_upsert_secrets_api import AirflowUpsertSecretsApi
from app.api.routers.data_ingest_api import DataIngestApi
from app.api.routers.mio_status_api import MioStatusApi
from app.api.routers.wf_exec_callback_api import WfExecCallbackApi
from app.api.security.callback_secret_auth import CallbackSecretAuth
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao
from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import SqlAlchemyAppWfExecLogDao
from app.core.dao.impl.sqlalchemy_data_ingest_dao import SqlAlchemyDataIngestDao
from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao
from app.core.dao.impl.sqlalchemy_dataset_location_dao import SqlAlchemyDatasetLocationDao
from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao
from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao
from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import SqlAlchemyMioIngestLogDao
from app.core.dao.mio_dao import MioDao
from app.core.dao.mio_dataset_dao import MioDatasetDao
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.impl.airflow_upsert_secrets_facade_impl import AirflowUpsertSecretsFacadeImpl
from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl
from app.core.facades.impl.tasks.airflow_upsert_secrets_call_service_task import (
    AirflowUpsertSecretsCallServiceTask,
)
from app.core.facades.impl.tasks.data_ingest_call_dao_task import DataIngestCallDaoTask
from app.core.facades.impl.tasks.data_ingest_collect_response_task import DataIngestCollectResponseTask
from app.core.facades.impl.tasks.data_ingest_prepare_dao_ctx_task import DataIngestPrepareDaoCtxTask
from app.core.facades.impl.tasks.data_ingest_validate_request_task import DataIngestValidateRequestTask
from app.core.facades.impl.tasks.mio_status_call_service_task import MioStatusCallServiceTask
from app.core.facades.impl.tasks.wf_exec_status_call_service_task import WfExecStatusCallServiceTask
from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl
from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade
from app.core.services.airflow_upsert_secrets_service import AirflowUpsertSecretsService
from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.impl.airflow_upsert_secrets_service_impl import AirflowUpsertSecretsServiceImpl
from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl
from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl
from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl
from app.core.services.mio_status_service import MioStatusService
from app.core.services.objects_factory import ServicesObjectsFactory
from app.core.services.wf_exec_status_service import WfExecStatusService
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
        (DaoObjectsFactory.get_app_wf_exec_log_dao, AppWfExecLogDao),
        (DaoObjectsFactory.get_dataset_dao, DatasetDao),
        (DaoObjectsFactory.get_dataset_location_dao, DatasetLocationDao),
        (DaoObjectsFactory.get_mio_dao, MioDao),
        (DaoObjectsFactory.get_mio_dataset_dao, MioDatasetDao),
        (DaoObjectsFactory.get_mio_ingest_log_dao, MioIngestLogDao),
        (DaoObjectsFactory.get_system_datasets_dao, SystemDatasetsDao),
        (DaoObjectsFactory.get_transaction_dao, TransactionDao),
        (ServicesObjectsFactory.get_dataset_status_service, DatasetStatusService),
        (ServicesObjectsFactory.get_mio_status_service, MioStatusService),
        (ServicesObjectsFactory.get_wf_exec_status_service, WfExecStatusService),
        (ServicesObjectsFactory.get_airflow_upsert_secrets_service, AirflowUpsertSecretsService),
        (FacadesObjectsFactory.get_mio_status_facade, MioStatusFacade),
        (FacadesObjectsFactory.get_wf_exec_status_facade, WfExecStatusFacade),
        (FacadesObjectsFactory.get_airflow_upsert_secrets_facade, AirflowUpsertSecretsFacade),
    ):
        assert getter() is getter()
        assert isinstance(getter(), interface)

    assert ApiObjectsFactory.get_app() is ApiObjectsFactory.get_app()
    assert ApiObjectsFactory.get_callback_secret_auth() is ApiObjectsFactory.get_callback_secret_auth()
    assert isinstance(ApiObjectsFactory.get_callback_secret_auth(), CallbackSecretAuth)
    assert ApiObjectsFactory.get_wf_exec_callback_api() is ApiObjectsFactory.get_wf_exec_callback_api()
    assert isinstance(ApiObjectsFactory.get_wf_exec_callback_api(), WfExecCallbackApi)
    assert ApiObjectsFactory.get_mio_status_api() is ApiObjectsFactory.get_mio_status_api()
    assert isinstance(ApiObjectsFactory.get_mio_status_api(), MioStatusApi)
    assert ApiObjectsFactory.get_airflow_upsert_secrets_api() is ApiObjectsFactory.get_airflow_upsert_secrets_api()
    assert isinstance(ApiObjectsFactory.get_airflow_upsert_secrets_api(), AirflowUpsertSecretsApi)


def test_the_classes_themselves_are_singletons():
    assert SqlAlchemyDataIngestDao() is SqlAlchemyDataIngestDao()
    assert SqlAlchemyAppWfDao() is SqlAlchemyAppWfDao()
    assert SqlAlchemyAppWfExecLogDao() is SqlAlchemyAppWfExecLogDao()
    assert SqlAlchemyDatasetDao() is SqlAlchemyDatasetDao()
    assert SqlAlchemyDatasetLocationDao() is SqlAlchemyDatasetLocationDao()
    assert SqlAlchemyMioDao() is SqlAlchemyMioDao()
    assert SqlAlchemyMioDatasetDao() is SqlAlchemyMioDatasetDao()
    assert SqlAlchemyMioIngestLogDao() is SqlAlchemyMioIngestLogDao()
    assert DataIngestApi() is DataIngestApi()
    assert WfExecCallbackApi() is WfExecCallbackApi()
    assert MioStatusApi() is MioStatusApi()
    assert AirflowUpsertSecretsApi() is AirflowUpsertSecretsApi()
    assert CallbackSecretAuth() is CallbackSecretAuth()
    assert DataIngestFacadeImpl() is DataIngestFacadeImpl()
    assert SqlAlchemySystemDatasetsDao() is SqlAlchemySystemDatasetsDao()
    assert SqlAlchemyTransactionDao() is SqlAlchemyTransactionDao()
    assert DatasetStatusServiceImpl() is DatasetStatusServiceImpl()
    assert MioStatusServiceImpl() is MioStatusServiceImpl()
    assert WfExecStatusServiceImpl() is WfExecStatusServiceImpl()
    assert AirflowUpsertSecretsServiceImpl() is AirflowUpsertSecretsServiceImpl()
    assert MioStatusFacadeImpl() is MioStatusFacadeImpl()
    assert WfExecStatusFacadeImpl() is WfExecStatusFacadeImpl()
    assert AirflowUpsertSecretsFacadeImpl() is AirflowUpsertSecretsFacadeImpl()
    for task in (
        DataIngestValidateRequestTask,
        DataIngestPrepareDaoCtxTask,
        DataIngestCallDaoTask,
        DataIngestCollectResponseTask,
        MioStatusCallServiceTask,
        WfExecStatusCallServiceTask,
        AirflowUpsertSecretsCallServiceTask,
    ):
        assert task() is task()


def test_one_object_even_when_many_threads_ask_at_once():
    with ThreadPoolExecutor(max_workers=16) as pool:
        daos = list(pool.map(lambda _: DaoObjectsFactory.get_data_ingest_dao(), range(200)))
        facades = list(pool.map(lambda _: FacadesObjectsFactory.get_data_ingest_facade(), range(200)))
    assert len({id(d) for d in daos}) == 1
    assert len({id(f) for f in facades}) == 1
