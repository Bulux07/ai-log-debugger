"""Python descriptions of the two tables. Alembic reads these to build migrations."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    """One row per API call to /analyze."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    filename: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    input_chars: Mapped[int]
    status: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[int | None]
    summary: Mapped[str | None] = mapped_column(Text)

    # Python-side shortcut: analysis.error_events gives the list of its errors.
    error_events: Mapped[list["ErrorEvent"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (Index("idx_analyses_created_at", "created_at"),)


class ErrorEvent(Base):
    """One row per distinct error found in a submitted log."""

    __tablename__ = "error_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE")
    )
    severity: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text)
    repeat_count: Mapped[int] = mapped_column(server_default=text("1"))

    analysis: Mapped["Analysis"] = relationship(back_populates="error_events")

    __table_args__ = (
        Index("idx_error_events_analysis_id", "analysis_id"),
        Index("idx_error_events_category", "category"),
    )