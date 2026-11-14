"""Database engine for the operational database (SQLite now; Postgres or similar by setting CCA_DB_URL)."""

from sqlalchemy import Connection, Engine, create_engine, event, text

from app.core.common.config import ALL_SCHEMAS, Settings, get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings())
    return _engine


def reset_engine() -> None:
    """Drop the cached engine (used by tests after they change the settings)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def _build_engine(settings: Settings) -> Engine:
    engine = create_engine(settings.db_url)
    if engine.dialect.name == "sqlite":
        settings.data_dir.mkdir(parents=True, exist_ok=True)

        @event.listens_for(engine, "connect")
        def _attach_schemas(dbapi_connection, _record):
            # SQLite has no schemas: attach one database file per schema, named after the schema.
            cursor = dbapi_connection.cursor()
            for schema in ALL_SCHEMAS:
                cursor.execute(f"ATTACH DATABASE '{settings.data_dir / (schema + '.sqlite')}' AS {schema}")
            cursor.close()

    return engine


def ensure_schemas(connection: Connection) -> None:
    """Create the schemas on databases that have real schemas. On SQLite, attaching already created them."""
    if connection.dialect.name == "sqlite":
        return
    for schema in ALL_SCHEMAS:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
