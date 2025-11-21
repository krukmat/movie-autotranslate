from app.models import Job, JobStage, JobStatus
from app.routes.metrics import (
    _mark_stage_event,
    _record_stage_history_metrics,
    _reset_stage_history_cache_for_tests,
)


def _build_job(stage_history: dict) -> Job:
    job = Job(
        external_id="job-1",
        asset_id=1,
        stage=JobStage.ASR,
        status=JobStatus.RUNNING,
        progress=0.0,
    )
    job.stage_history = stage_history
    return job


def test_mark_stage_event_deduplicates_entries() -> None:
    _reset_stage_history_cache_for_tests()
    assert _mark_stage_event("job", "ASR", "2024-01-01T00:00:00Z") is True
    assert _mark_stage_event("job", "ASR", "2024-01-01T00:00:00Z") is False


def test_record_stage_history_metrics_counts_new_entries() -> None:
    _reset_stage_history_cache_for_tests()
    stage_history = {
        JobStage.ASR.value: {"status": "success", "details": {"durationMs": 1200}, "updatedAt": "2024-01-01T00:00:00Z"},
        JobStage.ALIGN_MIX.value: {"status": "failed", "details": {"durationMs": 2500}, "updatedAt": "2024-01-01T01:00:00Z"},
    }
    job = _build_job(stage_history)

    recorded = _record_stage_history_metrics(job)
    assert recorded == 2

    recorded_again = _record_stage_history_metrics(job)
    assert recorded_again == 0
