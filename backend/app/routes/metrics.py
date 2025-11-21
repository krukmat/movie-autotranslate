from collections import deque
from threading import Lock
from typing import Deque, Tuple

from fastapi import APIRouter, Depends, Response

try:  # pragma: no cover - prometheus_client may be missing in unit test envs
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, generate_latest
except ImportError:  # pragma: no cover
    from typing import Any

    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"

    def generate_latest(_: Any) -> bytes:
        return b""

    class _NoOpMetric:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def labels(self, **_: str) -> "_NoOpMetric":
            return self

        def inc(self, *_: float, **__: float) -> None:
            return None

        def dec(self, *_: float, **__: float) -> None:
            return None

        def set(self, *_: float, **__: float) -> None:
            return None

        def observe(self, *_: float, **__: float) -> None:
            return None

    class Counter(_NoOpMetric):
        pass

    class Gauge(_NoOpMetric):
        pass

    class Histogram(_NoOpMetric):
        pass

    class _Registry:
        pass

    REGISTRY = _Registry()
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..models import Job, JobStage, JobStatus
from ..services import jobs as job_service

router = APIRouter()

_jobs_total = Gauge("jobs_total", "Jobs by status", ["status"])
_jobs_running = Gauge("jobs_running", "Jobs currently running")
_jobs_stage_active = Gauge("jobs_stage_active", "Jobs currently running per stage", ["stage"])
_stage_duration = Histogram(
    "api_stage_duration_seconds",
    "Stage durations derived from job history",
    ["stage"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)
_stage_failures = Counter("api_stage_failures_total", "Stage failures derived from job history", ["stage"])

_STAGE_HISTORY_CACHE_SIZE = 5000
_STAGE_HISTORY_SAMPLE = 200
_stage_history_lock = Lock()
_stage_history_events: set[Tuple[str, str, str]] = set()
_stage_history_order: Deque[Tuple[str, str, str]] = deque()


def _mark_stage_event(job_id: str, stage: str, updated_at: str | None) -> bool:
    if not updated_at:
        return False
    key = (job_id, stage, updated_at)
    with _stage_history_lock:
        if key in _stage_history_events:
            return False
        _stage_history_events.add(key)
        _stage_history_order.append(key)
        if len(_stage_history_order) > _STAGE_HISTORY_CACHE_SIZE:
            old_key = _stage_history_order.popleft()
            _stage_history_events.discard(old_key)
    return True


def _record_stage_history_metrics(job: Job) -> int:
    history = job.stage_history or {}
    recorded = 0
    for stage, info in history.items():
        updated_at = info.get("updatedAt")
        if not _mark_stage_event(job.external_id, stage, updated_at):
            continue
        details = info.get("details") or {}
        duration_ms = details.get("durationMs")
        if isinstance(duration_ms, (int, float)) and duration_ms > 0:
            _stage_duration.labels(stage=stage).observe(duration_ms / 1000.0)
        status = (info.get("status") or "").lower()
        if status == "failed":
            _stage_failures.labels(stage=stage).inc()
        recorded += 1
    return recorded


def _reset_stage_history_cache_for_tests() -> None:
    with _stage_history_lock:
        _stage_history_events.clear()
        _stage_history_order.clear()


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_session)) -> Response:
    status_counts = await job_service.count_jobs_by_status(session)
    stage_counts = await job_service.count_running_jobs_by_stage(session)

    for status in JobStatus:
        _jobs_total.labels(status=status.value.lower()).set(status_counts.get(status, 0))

    _jobs_running.set(status_counts.get(JobStatus.RUNNING, 0))

    for stage in JobStage:
        _jobs_stage_active.labels(stage=stage.value).set(stage_counts.get(stage, 0))

    recent_jobs = await job_service.fetch_recent_jobs(session, limit=_STAGE_HISTORY_SAMPLE)
    for job in recent_jobs:
        _record_stage_history_metrics(job)

    payload = generate_latest(REGISTRY)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
