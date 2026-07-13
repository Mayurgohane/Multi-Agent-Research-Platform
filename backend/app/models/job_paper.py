"""Association between research jobs and papers."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.paper import Paper
    from app.models.research_job import ResearchJob


class JobPaper(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_papers"
    __table_args__ = (UniqueConstraint("job_id", "paper_id", name="uq_job_papers_job_paper"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="candidate")

    job: Mapped[ResearchJob] = relationship("ResearchJob", back_populates="job_papers")
    paper: Mapped[Paper] = relationship("Paper", back_populates="job_links")
