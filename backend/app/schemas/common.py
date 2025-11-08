from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Languages = Literal["en", "es", "fr", "de"]


class StorageKeys(BaseModel):
    raw: Optional[str] = None
    processed: Optional[str] = None
    public: Optional[str] = None


class TimestampsModel(BaseModel):
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
