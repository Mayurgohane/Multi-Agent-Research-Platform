"""Academic paper model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.job_paper import JobPaper


class Paper(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "papers"
    __table_args__ = (
        UniqueConstraint("arxiv_id", name="uq_papers_arxiv_id"),
        UniqueConstraint("doi", name="uq_papers_doi"),
        UniqueConstraint("semantic_scholar_id", name="uq_papers_s2_id"),
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    venue: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    arxiv_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(256), nullable=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extractions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    job_links: Mapped[list[JobPaper]] = relationship(
        "JobPaper",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
