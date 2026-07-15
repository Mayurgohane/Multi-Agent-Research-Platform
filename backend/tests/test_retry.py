"""Tests for research job retry state transitions."""

from app.models.research_job import JobStatus, ResearchJob


def test_mark_queued_for_retry_resets_terminal_fields():
    job = ResearchJob(topic="Graph neural networks survey")
    job.mark_failed("upstream timeout")
    job.arq_job_id = "arq-123"

    assert job.status == JobStatus.FAILED.value
    assert job.error == "upstream timeout"
    assert job.completed_at is not None

    job.mark_queued_for_retry()

    assert job.status == JobStatus.QUEUED.value
    assert job.error is None
    assert job.started_at is None
    assert job.completed_at is None
    assert job.arq_job_id is None


def test_cancelled_job_can_be_reset_for_retry():
    job = ResearchJob(topic="RAG evaluation")
    job.mark_cancelled()
    job.mark_queued_for_retry()
    assert job.status == JobStatus.QUEUED.value
