from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Asset, Job, JobStage, JobStatus


def generate_job_id() -> str:
    return str(uuid.uuid4())


async def create_job(
    session: AsyncSession,
    *,
    asset: Asset,
    target_langs: List[str],
    presets: dict,
    requested_by: Optional[str],
) -> Job:
    job = Job(
        external_id=generate_job_id(),
        asset_id=asset.id,  # type: ignore[arg-type]
        stage=JobStage.ASR,
        status=JobStatus.PENDING,
        progress=0.0,
        target_langs=target_langs,
        presets=presets,
        requested_by=requested_by,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job_by_external_id(session: AsyncSession, external_id: str) -> Optional[Job]:
    result = await session.execute(select(Job).where(Job.external_id == external_id))
    return result.scalar_one_or_none()


async def update_job_stage(
    session: AsyncSession,
    *,
    job: Job,
    stage: JobStage,
    status: JobStatus,
    progress: float,
    error_message: Optional[str] = None,
) -> Job:
    job.stage = stage
    job.status = status
    job.progress = progress
    job.updated_at = datetime.utcnow()
    if status == JobStatus.RUNNING and job.started_at is None:
        job.started_at = datetime.utcnow()
    if status in {JobStatus.SUCCESS, JobStatus.FAILED}:
        job.ended_at = datetime.utcnow()
    job.error_message = error_message
    await session.commit()
    await session.refresh(job)
    return job


async def list_jobs(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[Job], int]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    offset = (page - 1) * page_size
    query = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(query)
    jobs = list(result.scalars())
    total = await session.scalar(select(func.count(Job.id)))
    return jobs, total or 0


async def reset_job_for_retry(
    session: AsyncSession,
    *,
    job: Job,
    resume_stage: JobStage,
) -> Job:
    job.stage = resume_stage
    job.status = JobStatus.PENDING
    job.progress = 0.0
    job.failed_stage = None
    job.error_message = None
    job.started_at = None
    job.ended_at = None
    job.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(job)
    return job


async def cancel_job(
    session: AsyncSession,
    *,
    job: Job,
    reason: str = "Cancelled",
) -> Job:
    job.status = JobStatus.CANCELLED
    job.failed_stage = job.stage
    job.error_message = reason
    job.progress = 1.0
    job.ended_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(job)
    return job


async def count_active_jobs_for_requester(session: AsyncSession, requested_by: Optional[str]) -> int:
    if not requested_by:
        return 0
    stmt = select(func.count(Job.id)).where(
        Job.requested_by == requested_by,
        Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
    )
    return await session.scalar(stmt) or 0
