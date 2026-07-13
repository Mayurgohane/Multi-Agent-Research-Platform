"""Critic routing tests."""

from app.agents.critic import should_continue_search


def test_continue_when_gaps():
    state = {
        "critic": {
            "should_continue": True,
            "additional_queries": ["graph neural networks survey 2023"],
        }
    }
    assert should_continue_search(state) == "searcher"


def test_writer_when_done():
    state = {"critic": {"should_continue": False, "additional_queries": []}}
    assert should_continue_search(state) == "writer"


def test_writer_when_continue_without_queries():
    state = {"critic": {"should_continue": True, "additional_queries": []}}
    assert should_continue_search(state) == "writer"
