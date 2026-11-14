"""The only module of the dao package that may import from dao/impl.

Static methods return the singleton, typed as the interface. Imports are lazy so a backend's library is only
needed when that backend is chosen.
"""

from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.mio_dao import MioDao
from app.core.dao.mio_dataset_dao import MioDatasetDao
from app.core.dao.system_datasets_dao import SystemDatasetsDao
from app.core.dao.transaction_dao import TransactionDao


class DaoObjectsFactory:
    @staticmethod
    def get_app_wf_dao() -> AppWfDao:
        from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao

        return SqlAlchemyAppWfDao()

    @staticmethod
    def get_app_wf_exec_log_dao() -> AppWfExecLogDao:
        from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import SqlAlchemyAppWfExecLogDao

        return SqlAlchemyAppWfExecLogDao()

    @staticmethod
    def get_dataset_dao() -> DatasetDao:
        from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao

        return SqlAlchemyDatasetDao()

    @staticmethod
    def get_dataset_location_dao() -> DatasetLocationDao:
        from app.core.dao.impl.sqlalchemy_dataset_location_dao import SqlAlchemyDatasetLocationDao

        return SqlAlchemyDatasetLocationDao()

    @staticmethod
    def get_mio_dao() -> MioDao:
        from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao

        return SqlAlchemyMioDao()

    @staticmethod
    def get_mio_dataset_dao() -> MioDatasetDao:
        from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao

        return SqlAlchemyMioDatasetDao()

    @staticmethod
    def get_data_ingest_dao() -> DataIngestDao:
        from app.core.dao.impl.sqlalchemy_data_ingest_dao import SqlAlchemyDataIngestDao

        return SqlAlchemyDataIngestDao()

    @staticmethod
    def get_system_datasets_dao() -> SystemDatasetsDao:
        from app.core.dao.impl.sqlalchemy_system_datasets_dao import SqlAlchemySystemDatasetsDao

        return SqlAlchemySystemDatasetsDao()

    @staticmethod
    def get_transaction_dao() -> TransactionDao:
        from app.core.dao.impl.sqlalchemy_transaction_dao import SqlAlchemyTransactionDao

        return SqlAlchemyTransactionDao()
