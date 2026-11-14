"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.facades.data_ingest_facade import DataIngestFacade


class FacadesObjectsFactory:
    @staticmethod
    def get_data_ingest_facade() -> DataIngestFacade:
        from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl

        return DataIngestFacadeImpl()
