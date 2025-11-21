import pytest

from workers.common.logging import stage_context
from workers.pipeline import tasks
from shared.models import JobStage


def test_parse_resume_defaults_to_asr() -> None:
    assert tasks._parse_resume(None) == JobStage.ASR
    assert tasks._parse_resume("UNKNOWN") == JobStage.ASR
    assert tasks._parse_resume(JobStage.TTS.value) == JobStage.TTS


def test_should_skip_stage_only_when_artifacts_ready() -> None:
    resume_stage = JobStage.TTS
    assert tasks._should_skip(JobStage.ASR, resume_stage, artifact_ready=True) is True
    assert tasks._should_skip(JobStage.ASR, resume_stage, artifact_ready=False) is False
    assert tasks._should_skip(JobStage.TTS, resume_stage, artifact_ready=True) is False


def test_stage_context_records_duration_on_success() -> None:
    with stage_context(job_id="job-1", asset_id="asset-1", stage="TEST") as timer:
        pass
    assert timer.duration_ms is not None


def test_stage_context_records_duration_on_failure() -> None:
    captured_timer = None

    with pytest.raises(RuntimeError):
        with stage_context(job_id="job-2", asset_id="asset-2", stage="FAIL") as timer:
            captured_timer = timer
            raise RuntimeError("boom")

    assert captured_timer is not None
    assert captured_timer.duration_ms is not None


def test_retry_state_computes_remaining_attempts() -> None:
    class DummyTask:
        max_retries = 3
        request = type("Req", (), {"retries": 1})()

    retries, will_retry = tasks._retry_state(DummyTask())
    assert retries == 1
    assert will_retry is True


def test_retry_state_without_limits() -> None:
    class DummyTask:
        max_retries = 0
        request = type("Req", (), {"retries": 0})()

    retries, will_retry = tasks._retry_state(DummyTask())
    assert retries == 0
    assert will_retry is False
