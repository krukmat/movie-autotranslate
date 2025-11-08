from datetime import datetime

from sqlmodel import select

from shared.models import Asset

from .db import get_session


def update_storage_keys(asset_external_id: str, storage_keys: dict) -> None:
    with get_session() as session:
        asset = session.exec(select(Asset).where(Asset.external_id == asset_external_id)).one()
        asset.storage_keys = storage_keys
        asset.updated_at = datetime.utcnow()
        session.add(asset)
        session.commit()
