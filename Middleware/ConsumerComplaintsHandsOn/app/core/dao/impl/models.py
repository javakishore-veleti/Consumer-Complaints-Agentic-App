"""SQLAlchemy table classes. They never leave dao/impl: everything above sees plain DTOs."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.common.config import SCHEMA_ADMIN


class Base(DeclarativeBase):
    pass


class AppWfModel(Base):
    __tablename__ = "app_workflows"
    __table_args__ = (
        UniqueConstraint("workflow_name", name="uq_app_workflows_workflow_name"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    engine_type: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # none_as_null: Python None is stored as SQL NULL, not as the JSON text "null".
    config: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AppWfExecLogModel(Base):
    __tablename__ = "app_workflows_exec_log"
    __table_args__ = (
        Index("ix_app_wf_exec_log_workflow_status", "workflow_id", "status"),
        Index("ix_app_wf_exec_log_mios_ingest_log_id", "mios_ingest_log_id"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D56): the log must survive a rename or delete of the workflow.
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # The next four are copied from app_workflows when the execution is requested and never change.
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    engine_type: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config_used: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    engine_run_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The MIO ingest this execution belongs to, or NULL (a workflow without a MIO). No foreign key (D58).
    mios_ingest_log_id: Mapped[str | None] = mapped_column(String(36))


class DatasetModel(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("name", name="uq_datasets_name"),
        UniqueConstraint("code", name="uq_datasets_code"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # The short code builds the local env var name LOCAL_DATA_PATH_<code> (D57).
    code: Mapped[str] = mapped_column(String(15), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DatasetLocationModel(Base):
    __tablename__ = "datasets_location"
    __table_args__ = (
        UniqueConstraint("dataset_id", "location_type", "path", name="uq_datasets_location_dataset_type_path"),
        UniqueConstraint("dataset_id", "local_env_var_name", name="uq_datasets_location_dataset_env_var"),
        CheckConstraint(
            "(path IS NOT NULL AND local_env_var_name IS NULL) OR (path IS NULL AND local_env_var_name IS NOT NULL)",
            name="ck_datasets_location_path_xor_env",
        ),
        Index("ix_datasets_location_dataset_id", "dataset_id"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D57): the DAOs keep the parent rule.
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    location_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # A literal path or URL, or NULL when local_env_var_name is set (exactly one of the two).
    path: Mapped[str | None] = mapped_column(String(1000))
    # Only the NAME of an environment variable, only for type "local". Never a value.
    local_env_var_name: Mapped[str | None] = mapped_column(String(64))
    # A name that points to a secret held elsewhere. Never the secret.
    credentials_ref: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MioModel(Base):
    __tablename__ = "mios"
    __table_args__ = (
        UniqueConstraint("name", name="uq_mios_name"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # The name and description are labels for people. No code reads them to choose data (D57).
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MioDatasetModel(Base):
    __tablename__ = "mios_datasets"
    __table_args__ = (
        UniqueConstraint("mio_id", "dataset_id", name="uq_mios_datasets_mio_dataset"),
        Index("ix_mios_datasets_mio_id", "mio_id"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # The chosen location of that dataset for that MIO. Many MIOs may choose the same one.
    dataset_location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MioIngestLogModel(Base):
    __tablename__ = "mios_ingest_log"
    __table_args__ = (
        Index("ix_mios_ingest_log_mio_status", "mio_id", "status"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D57, D58): the DAO checks the MIO on create.
    mio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Volume (D58): notes that may be set on any row, also a final one.
    rows_loaded: Mapped[int | None] = mapped_column(BigInteger)
    batch_count: Mapped[int | None] = mapped_column(Integer)
    # An opaque marker of how far an incremental ingest got. No code reads inside it.
    increment_marker: Mapped[str | None] = mapped_column(String(255))
