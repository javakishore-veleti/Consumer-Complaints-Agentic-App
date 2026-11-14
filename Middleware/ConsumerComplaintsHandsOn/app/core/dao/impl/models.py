"""SQLAlchemy table classes. They never leave dao/impl: everything above sees plain DTOs."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.common.config import SCHEMA_COMPLAINTS


class Base(DeclarativeBase):
    pass


class DataIngestLogModel(Base):
    __tablename__ = "data_ingest_log"
    __table_args__ = (
        Index("ix_data_ingest_log_purpose_status", "purpose", "status"),
        {"schema": SCHEMA_COMPLAINTS},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(128))
    message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SystemDatasetModel(Base):
    __tablename__ = "system_datasets"
    __table_args__ = {"schema": SCHEMA_COMPLAINTS}

    dataset: Mapped[str] = mapped_column(String(32), primary_key=True)
    stage: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_log_id: Mapped[str | None] = mapped_column(String(36))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
