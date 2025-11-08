from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from shared.models import Job, JobStage, JobStatus

from .db import get_session


def update_job(
    job_external_id: str,
    *,
    stage: JobStage,
    status: JobStatus,
    progress: float,
    error_message: str | None = None,
    failed_stage: JobStage | None = None,
) -> None:
    with get_session() as session:
        result = session.exec(select(Job).where(Job.external_id == job_external_id))
        job = result.one()
        job.stage = stage
        job.status = status
        job.progress = progress
        job.updated_at = datetime.utcnow()
        if status == JobStatus.RUNNING and job.started_at is None:
            job.started_at = datetime.utcnow()
        if status in {JobStatus.SUCCESS, JobStatus.FAILED}:
            job.ended_at = datetime.utcnow()
        job.error_message = error_message
        job.failed_stage = failed_stage
        session.add(job)
        session.commit()


def mark_success(job_external_id: str) -> None:
    update_job(job_external_id, stage=JobStage.DONE, status=JobStatus.SUCCESS, progress=1.0)


def mark_failure(job_external_id: str, stage: JobStage, message: str) -> None:
    update_job(
        job_external_id,
        stage=stage,
        status=JobStatus.FAILED,
        progress=0.0,
        error_message=message,
        failed_stage=stage,
    )
