from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..models import Asset, Job, JobStage, JobStatus
from ..schemas.jobs import (
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobRetryRequest,
)
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
        logsKey=job.logs_key,
        stageHistory=job.stage_history or {},
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    jobs, total = await job_service.list_jobs(session, page=page, page_size=page_size)
    responses: list[JobResponse] = []
    for job in jobs:
        asset = await session.get(Asset, job.asset_id)
        asset_external_id = asset.external_id if asset else str(job.asset_id)
        responses.append(map_job(job, asset_external_id))
    return JobListResponse(items=responses, total=total, page=page, page_size=page_size)


@router.post("/translate", response_model=JobResponse)
async def create_translation_job(
    payload: JobCreateRequest,
    request: Request,
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

    client_id = _client_id(request)
    if settings.max_active_jobs_per_key > 0 and client_id != "anonymous":
        active = await job_service.count_active_jobs_for_requester(session, client_id)
        if active >= settings.max_active_jobs_per_key:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Job quota exceeded for this API key.",
            )

    job = await job_service.create_job(
        session,
        asset=asset,
        target_langs=payload.target_langs,
        presets=payload.presets,
        requested_by=client_id if client_id != "anonymous" else None,
    )
    resume_value = payload.resume_from.value if payload.resume_from else None
    enqueue_pipeline_job(job_external_id=job.external_id, resume_from=resume_value)
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


def _parse_stage(value: Optional[JobStage]) -> JobStage:
    return value or JobStage.ASR


def _client_id(request: Request) -> str:
    return getattr(request.state, "client_id", "anonymous")


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    payload: JobRetryRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    job = await job_service.get_job_by_external_id(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    resume_stage = _parse_stage(payload.resume_from)
    client_id = _client_id(request)
    if job.requested_by and client_id != job.requested_by:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot retry jobs created by another API key.")
    await job_service.reset_job_for_retry(session, job=job, resume_stage=resume_stage)
    enqueue_pipeline_job(job_external_id=job.external_id, resume_from=resume_stage.value)
    asset = await session.get(Asset, job.asset_id)
    asset_external_id = asset.external_id if asset else str(job.asset_id)
    return map_job(job, asset_external_id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def cancel_job(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    job = await job_service.get_job_by_external_id(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    if job.status == JobStatus.SUCCESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed jobs cannot be cancelled.")
    client_id = _client_id(request)
    if job.requested_by and client_id != job.requested_by:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel jobs created by another API key.")
    await job_service.cancel_job(session, job=job)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
