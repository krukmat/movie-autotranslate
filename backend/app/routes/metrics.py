from fastapi import APIRouter, Depends, Response
from prometheus_client import REGISTRY, CONTENT_TYPE_LATEST, Gauge, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..services import jobs as job_service

router = APIRouter()

_jobs_total = Gauge("jobs_total", "Jobs by status", ["status"])
_jobs_running = Gauge("jobs_running", "Jobs currently running")
_jobs_stage_active = Gauge("jobs_stage_active", "Jobs currently running per stage", ["stage"])


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_session)) -> Response:
    jobs = await job_service.list_jobs(session)
    running = sum(1 for job in jobs if job.status == job.status.RUNNING)
    success = sum(1 for job in jobs if job.status == job.status.SUCCESS)
    failed = sum(1 for job in jobs if job.status == job.status.FAILED)

    _jobs_running.set(running)
    _jobs_total.labels(status="success").set(success)
    _jobs_total.labels(status="failed").set(failed)

    stage_counts = {}
    for job in jobs:
        stage_counts[job.stage.value] = stage_counts.get(job.stage.value, 0) + (1 if job.status == job.status.RUNNING else 0)
    for stage, count in stage_counts.items():
        _jobs_stage_active.labels(stage=stage).set(count)

    payload = generate_latest(REGISTRY)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
