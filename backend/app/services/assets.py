from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Asset


def generate_asset_id() -> str:
    return str(uuid.uuid4())


async def create_asset(
    session: AsyncSession,
    *,
    user_id: Optional[str],
    src_lang: Optional[str],
    target_langs: List[str],
    storage_keys: Dict[str, str],
    duration_sec: Optional[float],
) -> Asset:
    asset = Asset(
        external_id=generate_asset_id(),
        user_id=user_id,
        src_lang=src_lang,
        target_langs=target_langs,
        storage_keys=storage_keys,
        duration_sec=duration_sec,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


async def upsert_asset_by_external_id(
    session: AsyncSession,
    *,
    external_id: str,
    user_id: Optional[str],
    src_lang: Optional[str],
    target_langs: List[str],
    storage_keys: Dict[str, str],
    duration_sec: Optional[float],
) -> Asset:
    result = await session.execute(select(Asset).where(Asset.external_id == external_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        asset = Asset(
            external_id=external_id,
            user_id=user_id,
            src_lang=src_lang,
            target_langs=target_langs,
            storage_keys=storage_keys,
            duration_sec=duration_sec,
        )
        session.add(asset)
    else:
        asset.storage_keys = {**asset.storage_keys, **storage_keys}
        asset.target_langs = target_langs or asset.target_langs
        asset.src_lang = src_lang or asset.src_lang
        asset.duration_sec = duration_sec or asset.duration_sec
        asset.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(asset)
    return asset


async def list_assets(session: AsyncSession) -> List[Asset]:
    result = await session.execute(select(Asset))
    return list(result.scalars())


async def get_asset_by_external_id(session: AsyncSession, external_id: str) -> Optional[Asset]:
    result = await session.execute(select(Asset).where(Asset.external_id == external_id))
    return result.scalar_one_or_none()
