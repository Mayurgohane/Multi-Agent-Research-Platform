"""Pytest fixtures."""

from __future__ import annotations

import os

import pytest

# Ensure settings load in test mode before app imports
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://marp:marp@localhost:5432/marp_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")


@pytest.fixture
def sample_papers():
    from app.services.paper_dto import PaperRecord

    return [
        PaperRecord(
            title="Attention Is All You Need",
            abstract="We propose the Transformer.",
            authors=["Vaswani et al."],
            year=2017,
            source="semantic_scholar",
            doi="10.5555/3295222.3295349",
            citation_count=100000,
        ),
        PaperRecord(
            title="Attention is all you need!",
            abstract="Transformer architecture.",
            authors=["Ashish Vaswani"],
            year=2017,
            source="arxiv",
            arxiv_id="1706.03762",
            doi="10.5555/3295222.3295349",
            citation_count=50,
        ),
        PaperRecord(
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            abstract="BERT model",
            authors=["Devlin et al."],
            year=2019,
            source="arxiv",
            arxiv_id="1810.04805",
        ),
    ]
