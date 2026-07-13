"""Bibliography helper tests."""

from app.agents.writer import _build_bibliography


def test_build_bibliography():
    papers = [
        {
            "title": "Paper A",
            "authors": ["Alice", "Bob", "Carol", "Dave"],
            "year": 2024,
            "url": "https://example.com/a",
            "doi": "10.1/a",
        }
    ]
    bib = _build_bibliography(papers)
    assert "1" in bib["citation_map"]
    assert "et al." in bib["lines"][0]
    assert "Paper A" in bib["lines"][0]
