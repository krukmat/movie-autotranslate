from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..schemas.assets import AssetResponse
from ..services import assets as asset_service
from ..services import storage

router = APIRouter(prefix="/assets", tags=["assets"])
settings = get_settings()


def _map_asset(asset) -> AssetResponse:
    outputs = {}
    public_key = asset.storage_keys.get("public")
    if public_key:
        outputs["hls"] = storage.build_signed_url(public_key, bucket=settings.minio_bucket_public)
    return AssetResponse(
        id=asset.id,
        assetId=asset.external_id,
        userId=asset.user_id,
        srcLang=asset.src_lang,
        targetLangs=asset.target_langs,
        storageKeys=asset.storage_keys,
        durationSec=asset.duration_sec,
        createdAt=asset.created_at,
        updatedAt=asset.updated_at,
        outputs=outputs,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    session: AsyncSession = Depends(get_session),
) -> AssetResponse:
    asset = await asset_service.get_asset_by_external_id(session, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return _map_asset(asset)


@router.get("/{asset_id}/hls/master.m3u8")
async def get_asset_master_playlist(
    asset_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    asset = await asset_service.get_asset_by_external_id(session, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    public_key = asset.storage_keys.get("public")
    if not public_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published HLS master for asset.",
        )

    return {
        "assetId": asset.external_id,
        "masterUrl": storage.build_signed_url(public_key, bucket=settings.minio_bucket_public),
    }
