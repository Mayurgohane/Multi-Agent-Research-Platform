"""Research schema validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.research import ResearchCreateRequest


def test_research_create_valid():
    req = ResearchCreateRequest(topic="Large language model evaluation")
    assert req.max_papers is None
    assert "language" in req.topic


def test_research_create_topic_too_short():
    with pytest.raises(ValidationError):
        ResearchCreateRequest(topic="AI")
