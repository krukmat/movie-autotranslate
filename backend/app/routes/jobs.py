from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..models import Asset, Job
from ..schemas.jobs import JobCreateRequest, JobResponse
from ..services import assets as asset_service
from ..services import jobs as job_service
from ..queue import enqueue_pipeline_job

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()


def map_job(job: Job, asset_external_id: str) -> JobResponse:
    return JobResponse(
        jobId=job.external_id,
        assetId=asset_external_id,
        stage=job.stage,
        status=job.status,
        progress=job.progress,
        startedAt=job.started_at,
        endedAt=job.ended_at,
        failedStage=job.failed_stage,
        errorMessage=job.error_message,
        targetLangs=job.target_langs,
        presets=job.presets,
    )


@router.get("", response_model=list[JobResponse])
async def list_jobs(session: AsyncSession = Depends(get_session)) -> list[JobResponse]:
    jobs = await job_service.list_jobs(session)
    responses: list[JobResponse] = []
    for job in jobs:
        asset = await session.get(Asset, job.asset_id)
        asset_external_id = asset.external_id if asset else str(job.asset_id)
        responses.append(map_job(job, asset_external_id))
    return responses


@router.post("/translate", response_model=JobResponse)
async def create_translation_job(
    payload: JobCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    asset = await asset_service.get_asset_by_external_id(session, payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    for language in payload.target_langs:
        if language not in settings.allowed_languages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported language requested: {language}",
            )

    if not asset.target_langs:
        asset.target_langs = payload.target_langs
        session.add(asset)
        await session.commit()

    job = await job_service.create_job(
        session,
        asset=asset,
        target_langs=payload.target_langs,
        presets=payload.presets,
    )
    enqueue_pipeline_job(job_external_id=job.external_id, resume_from=payload.resume_from)
    return map_job(job, asset.external_id)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    job = await job_service.get_job_by_external_id(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    asset = await session.get(Asset, job.asset_id)
    asset_external_id = asset.external_id if asset else str(job.asset_id)
    return map_job(job, asset_external_id)
