from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import Languages, StorageKeys


class AssetBase(BaseModel):
    user_id: Optional[str] = Field(default=None, alias="userId")
    src_lang: Optional[Languages] = Field(default=None, alias="srcLang")
    target_langs: List[Languages] = Field(default_factory=list, alias="targetLangs")

    class Config:
        allow_population_by_field_name = True


class AssetCreateRequest(BaseModel):
    asset_id: str = Field(alias="assetId")
    user_id: Optional[str] = Field(default=None, alias="userId")
    src_lang: Optional[Languages] = Field(default=None, alias="srcLang")
    target_langs: List[Languages] = Field(default_factory=list, alias="targetLangs")
    storage_keys: Optional[Dict[str, str]] = Field(default=None, alias="storageKeys")
    duration_sec: Optional[float] = Field(default=None, alias="durationSec")

    class Config:
        allow_population_by_field_name = True


class AssetResponse(AssetBase):
    id: int
    asset_id: str = Field(alias="assetId")
    storage_keys: StorageKeys = Field(alias="storageKeys")
    duration_sec: Optional[float] = Field(default=None, alias="durationSec")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    outputs: Dict[str, str] = Field(default_factory=dict)

    class Config:
        allow_population_by_field_name = True
