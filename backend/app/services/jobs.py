from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
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
) -> Job:
    job = Job(
        external_id=generate_job_id(),
        asset_id=asset.id,  # type: ignore[arg-type]
        stage=JobStage.ASR,
        status=JobStatus.PENDING,
        progress=0.0,
        target_langs=target_langs,
        presets=presets,
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


async def list_jobs_for_asset(session: AsyncSession, asset: Asset) -> List[Job]:
    result = await session.execute(select(Job).where(Job.asset_id == asset.id))
    return list(result.scalars())


async def list_jobs(session: AsyncSession, limit: int = 50) -> List[Job]:
    result = await session.execute(select(Job).order_by(Job.created_at.desc()).limit(limit))
    return list(result.scalars())
