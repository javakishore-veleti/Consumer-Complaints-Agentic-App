"""The only module of the dao package that may import from dao/impl.

Static methods return the singleton, typed as the interface. Imports are lazy so a backend's library is only
needed when that backend is chosen.
"""

from app.core.dao.data_ingest_dao import DataIngestDao


class DaoObjectsFactory:
    @staticmethod
    def get_data_ingest_dao() -> DataIngestDao:
        from app.core.dao.impl.sqlalchemy_data_ingest_dao import SqlAlchemyDataIngestDao

        return SqlAlchemyDataIngestDao()
