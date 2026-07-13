"""Tests for paper deduplication."""

from app.services.paper_dto import PaperRecord, dedupe_papers, normalize_title


def test_normalize_title():
    assert normalize_title("Attention Is All You Need!") == "attention is all you need"


def test_dedupe_by_doi(sample_papers):
    result = dedupe_papers(sample_papers)
    assert len(result) == 2
    attention = next(p for p in result if "attention" in p.title.lower())
    assert attention.arxiv_id == "1706.03762"
    assert attention.citation_count == 100000
    assert attention.source == "merged"


def test_dedupe_by_title_only():
    papers = [
        PaperRecord(title="Same Title", source="arxiv", arxiv_id="1"),
        PaperRecord(title="Same Title", source="semantic_scholar", semantic_scholar_id="abc"),
    ]
    result = dedupe_papers(papers)
    assert len(result) == 1
    assert result[0].arxiv_id == "1"
    assert result[0].semantic_scholar_id == "abc"
