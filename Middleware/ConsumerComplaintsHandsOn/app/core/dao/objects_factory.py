"""The only module of the dao package that may import from dao/impl.

Static methods return the singleton, typed as the interface. Imports are lazy so a backend's library is only
needed when that backend is chosen.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.dao.app_endpoint_dao import AppEndpointDao
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.dataset_import_run_dao import DatasetImportRunDao
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.mio_acl_dao import MioAclDao
from app.core.dao.mio_dao import MioDao
from app.core.dao.mio_dataset_dao import MioDatasetDao
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao
from app.core.dao.mio_workflow_dao import MioWorkflowDao
from app.core.dao.transaction_dao import TransactionDao
from app.core.dao.zone_ingest_log_dao import ZoneIngestLogDao

_DAO_INTERFACES = (
    AppWfDao,
    AppWfExecLogDao,
    AppEndpointDao,
    DatasetDao,
    DatasetImportRunDao,
    DatasetLocationDao,
    MioDao,
    MioDatasetDao,
    MioIngestLogDao,
    MioWorkflowDao,
    MioAclDao,
    TransactionDao,
    ZoneIngestLogDao,
)


class DaoObjectsFactory:
    _initialized = False
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if DaoObjectsFactory._initialized:
            return
        with DaoObjectsFactory._lock:
            if DaoObjectsFactory._initialized:
                return
            from app.core.common.config import get_settings

            # D75/D79: DaoObjectsFactory chooses the impl from Settings.operational_store.
            store = get_settings().operational_store
            if store == "mongodb":
                from app.core.dao.impl.mongo.mongo_app_endpoint_dao import (
                    MongoAppEndpointDao,
                )
                from app.core.dao.impl.mongo.mongo_app_wf_dao import MongoAppWfDao
                from app.core.dao.impl.mongo.mongo_app_wf_exec_log_dao import (
                    MongoAppWfExecLogDao,
                )
                from app.core.dao.impl.mongo.mongo_dataset_dao import MongoDatasetDao
                from app.core.dao.impl.mongo.mongo_dataset_import_run_dao import (
                    MongoDatasetImportRunDao,
                )
                from app.core.dao.impl.mongo.mongo_dataset_location_dao import (
                    MongoDatasetLocationDao,
                )
                from app.core.dao.impl.mongo.mongo_mio_acl_dao import MongoMioAclDao
                from app.core.dao.impl.mongo.mongo_mio_dao import MongoMioDao
                from app.core.dao.impl.mongo.mongo_mio_dataset_dao import (
                    MongoMioDatasetDao,
                )
                from app.core.dao.impl.mongo.mongo_mio_ingest_log_dao import (
                    MongoMioIngestLogDao,
                )
                from app.core.dao.impl.mongo.mongo_mio_workflow_dao import (
                    MongoMioWorkflowDao,
                )
                from app.core.dao.impl.mongo.mongo_transaction_dao import (
                    MongoTransactionDao,
                )
                from app.core.dao.impl.mongo.mongo_zone_ingest_log_dao import (
                    MongoZoneIngestLogDao,
                )

                bean_registry.register(AppWfDao, MongoAppWfDao())
                bean_registry.register(AppWfExecLogDao, MongoAppWfExecLogDao())
                bean_registry.register(AppEndpointDao, MongoAppEndpointDao())
                bean_registry.register(DatasetDao, MongoDatasetDao())
                bean_registry.register(DatasetImportRunDao, MongoDatasetImportRunDao())
                bean_registry.register(DatasetLocationDao, MongoDatasetLocationDao())
                bean_registry.register(MioDao, MongoMioDao())
                bean_registry.register(MioDatasetDao, MongoMioDatasetDao())
                bean_registry.register(MioIngestLogDao, MongoMioIngestLogDao())
                bean_registry.register(MioWorkflowDao, MongoMioWorkflowDao())
                bean_registry.register(MioAclDao, MongoMioAclDao())
                bean_registry.register(TransactionDao, MongoTransactionDao())
                bean_registry.register(ZoneIngestLogDao, MongoZoneIngestLogDao())
            else:
                from app.core.dao.impl.sqlalchemy_app_endpoint_dao import (
                    SqlAlchemyAppEndpointDao,
                )
                from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao
                from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import (
                    SqlAlchemyAppWfExecLogDao,
                )
                from app.core.dao.impl.sqlalchemy_dataset_dao import (
                    SqlAlchemyDatasetDao,
                )
                from app.core.dao.impl.sqlalchemy_dataset_import_run_dao import (
                    SqlAlchemyDatasetImportRunDao,
                )
                from app.core.dao.impl.sqlalchemy_dataset_location_dao import (
                    SqlAlchemyDatasetLocationDao,
                )
                from app.core.dao.impl.sqlalchemy_mio_acl_dao import SqlAlchemyMioAclDao
                from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao
                from app.core.dao.impl.sqlalchemy_mio_dataset_dao import (
                    SqlAlchemyMioDatasetDao,
                )
                from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import (
                    SqlAlchemyMioIngestLogDao,
                )
                from app.core.dao.impl.sqlalchemy_mio_workflow_dao import (
                    SqlAlchemyMioWorkflowDao,
                )
                from app.core.dao.impl.sqlalchemy_transaction_dao import (
                    SqlAlchemyTransactionDao,
                )
                from app.core.dao.impl.sqlalchemy_zone_ingest_log_dao import (
                    SqlAlchemyZoneIngestLogDao,
                )

                bean_registry.register(AppWfDao, SqlAlchemyAppWfDao())
                bean_registry.register(AppWfExecLogDao, SqlAlchemyAppWfExecLogDao())
                bean_registry.register(AppEndpointDao, SqlAlchemyAppEndpointDao())
                bean_registry.register(DatasetDao, SqlAlchemyDatasetDao())
                bean_registry.register(DatasetImportRunDao, SqlAlchemyDatasetImportRunDao())
                bean_registry.register(DatasetLocationDao, SqlAlchemyDatasetLocationDao())
                bean_registry.register(MioDao, SqlAlchemyMioDao())
                bean_registry.register(MioDatasetDao, SqlAlchemyMioDatasetDao())
                bean_registry.register(MioIngestLogDao, SqlAlchemyMioIngestLogDao())
                bean_registry.register(MioWorkflowDao, SqlAlchemyMioWorkflowDao())
                bean_registry.register(MioAclDao, SqlAlchemyMioAclDao())
                bean_registry.register(TransactionDao, SqlAlchemyTransactionDao())
                bean_registry.register(ZoneIngestLogDao, SqlAlchemyZoneIngestLogDao())
            DaoObjectsFactory._initialized = True

    @staticmethod
    def reset() -> None:
        """Clear registered DAO beans so the next init() can pick a different store (tests)."""
        with DaoObjectsFactory._lock:
            for interface in _DAO_INTERFACES:
                bean_registry._by_interface.pop(interface, None)
            DaoObjectsFactory._initialized = False

    @staticmethod
    def get_app_wf_dao() -> AppWfDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(AppWfDao)  # type: ignore[return-value]

    @staticmethod
    def get_app_wf_exec_log_dao() -> AppWfExecLogDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(AppWfExecLogDao)  # type: ignore[return-value]

    @staticmethod
    def get_dataset_dao() -> DatasetDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(DatasetDao)  # type: ignore[return-value]

    @staticmethod
    def get_dataset_location_dao() -> DatasetLocationDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(DatasetLocationDao)  # type: ignore[return-value]

    @staticmethod
    def get_dataset_import_run_dao() -> DatasetImportRunDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(DatasetImportRunDao)  # type: ignore[return-value]

    @staticmethod
    def get_app_endpoint_dao() -> AppEndpointDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(AppEndpointDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_dao() -> MioDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_dataset_dao() -> MioDatasetDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioDatasetDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_workflow_dao() -> MioWorkflowDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioWorkflowDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_acl_dao() -> MioAclDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioAclDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_ingest_log_dao() -> MioIngestLogDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioIngestLogDao)  # type: ignore[return-value]

    @staticmethod
    def get_transaction_dao() -> TransactionDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(TransactionDao)  # type: ignore[return-value]

    @staticmethod
    def get_zone_ingest_log_dao() -> ZoneIngestLogDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(ZoneIngestLogDao)  # type: ignore[return-value]
