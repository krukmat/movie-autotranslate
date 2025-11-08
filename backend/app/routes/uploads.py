from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..schemas.uploads import (
    UploadCompleteRequest,
    UploadInitRequest,
    UploadInitResponse,
)
from ..services import assets as asset_service
from ..services import storage

router = APIRouter(prefix="/upload", tags=["uploads"])
settings = get_settings()


@router.post("/init", response_model=UploadInitResponse)
async def init_upload(
    payload: UploadInitRequest,
    session: AsyncSession = Depends(get_session),
) -> UploadInitResponse:
    if payload.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds configured maximum upload size.",
        )
    upload_id, object_name = storage.init_multipart_upload(
        filename=payload.filename,
        content_type=payload.content_type,
    )
    parts = storage.get_presigned_parts(
        object_name=object_name,
        upload_id=upload_id,
        total_size=payload.size,
    )
    asset_id = asset_service.generate_asset_id()
    await asset_service.upsert_asset_by_external_id(
        session,
        external_id=asset_id,
        user_id=None,
        src_lang=None,
        target_langs=[],
        storage_keys={"raw": object_name},
        duration_sec=None,
    )
    return UploadInitResponse(
        assetId=asset_id,
        uploadId=upload_id,
        partSize=settings.upload_part_size,
        parts=parts,
    )


@router.post("/complete")
async def complete_upload(
    payload: UploadCompleteRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    asset = await asset_service.get_asset_by_external_id(session, payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    object_name = asset.storage_keys.get("raw")
    if object_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload not initialized correctly for asset.",
        )

    storage.complete_multipart_upload(object_name, payload.upload_id, payload.etags)
    asset = await asset_service.upsert_asset_by_external_id(
        session,
        external_id=payload.asset_id,
        user_id=asset.user_id,
        src_lang=payload.src_lang,
        target_langs=payload.target_langs,
        storage_keys=asset.storage_keys,
        duration_sec=asset.duration_sec,
    )
    return {"assetId": asset.external_id, "status": "UPLOAD_COMPLETED"}
