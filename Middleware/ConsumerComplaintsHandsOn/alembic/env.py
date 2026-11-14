"""Alembic environment. The database comes from app settings (CCA_DB_URL / CCA_DATA_DIR), not from alembic.ini,
so the API and the migrations always talk to the same database."""

from logging.config import fileConfig

from alembic import context

from app.core.common.config import ALL_SCHEMAS, get_settings
from app.core.dao.impl.database import ensure_schemas, get_engine
from app.core.dao.impl.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _include_name(name, type_, parent_names):
    # Only look at our own schemas.
    if type_ == "schema":
        return name in ALL_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Emit the SQL instead of running it: alembic upgrade head --sql"""
    context.configure(
        url=get_settings().db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        ensure_schemas(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=_include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
