"""The only module of the dao package that may import from dao/impl.

Static methods return the singleton, typed as the interface. Imports are lazy so a backend's library is only
needed when that backend is chosen.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.mio_dao import MioDao
from app.core.dao.mio_dataset_dao import MioDatasetDao
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao
from app.core.dao.transaction_dao import TransactionDao


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
            from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao
            from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import (
                SqlAlchemyAppWfExecLogDao,
            )
            from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao
            from app.core.dao.impl.sqlalchemy_dataset_location_dao import (
                SqlAlchemyDatasetLocationDao,
            )
            from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao
            from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao
            from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import (
                SqlAlchemyMioIngestLogDao,
            )
            from app.core.dao.impl.sqlalchemy_transaction_dao import SqlAlchemyTransactionDao

            bean_registry.register(AppWfDao, SqlAlchemyAppWfDao())
            bean_registry.register(AppWfExecLogDao, SqlAlchemyAppWfExecLogDao())
            bean_registry.register(DatasetDao, SqlAlchemyDatasetDao())
            bean_registry.register(DatasetLocationDao, SqlAlchemyDatasetLocationDao())
            bean_registry.register(MioDao, SqlAlchemyMioDao())
            bean_registry.register(MioDatasetDao, SqlAlchemyMioDatasetDao())
            bean_registry.register(MioIngestLogDao, SqlAlchemyMioIngestLogDao())
            bean_registry.register(TransactionDao, SqlAlchemyTransactionDao())
            DaoObjectsFactory._initialized = True

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
    def get_mio_dao() -> MioDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_dataset_dao() -> MioDatasetDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioDatasetDao)  # type: ignore[return-value]

    @staticmethod
    def get_mio_ingest_log_dao() -> MioIngestLogDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(MioIngestLogDao)  # type: ignore[return-value]

    @staticmethod
    def get_transaction_dao() -> TransactionDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(TransactionDao)  # type: ignore[return-value]
