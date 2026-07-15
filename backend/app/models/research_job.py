"""Research job model."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.agent_event import AgentEvent
    from app.models.job_paper import JobPaper
    from app.models.report import Report


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "research_jobs"

    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobStatus.QUEUED.value,
        index=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arq_job_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    events: Mapped[list[AgentEvent]] = relationship(
        "AgentEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="AgentEvent.created_at",
    )
    job_papers: Mapped[list[JobPaper]] = relationship(
        "JobPaper",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    report: Mapped[Report | None] = relationship(
        "Report",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def mark_running(self) -> None:
        from datetime import timezone

        self.status = JobStatus.RUNNING.value
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        from datetime import timezone

        self.status = JobStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)
        self.error = None

    def mark_failed(self, error: str) -> None:
        from datetime import timezone

        self.status = JobStatus.FAILED.value
        self.completed_at = datetime.now(timezone.utc)
        self.error = error

    def mark_cancelled(self) -> None:
        from datetime import timezone

        self.status = JobStatus.CANCELLED.value
        self.completed_at = datetime.now(timezone.utc)

    def mark_queued_for_retry(self) -> None:
        """Reset terminal job state so it can be re-enqueued."""
        self.status = JobStatus.QUEUED.value
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.arq_job_id = None
