from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ..models import JobStage, JobStatus
from .common import Languages


class JobCreateRequest(BaseModel):
    asset_id: str = Field(alias="assetId")
    target_langs: List[Languages] = Field(alias="targetLangs")
    presets: Dict[str, str] = Field(default_factory=dict)
    resume_from: Optional[JobStage] = Field(default=None, alias="resumeFrom")

    class Config:
        allow_population_by_field_name = True


class JobResponse(BaseModel):
    job_id: str = Field(alias="jobId")
    asset_id: str = Field(alias="assetId")
    stage: JobStage
    status: JobStatus
    progress: float
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    ended_at: Optional[datetime] = Field(default=None, alias="endedAt")
    failed_stage: Optional[JobStage] = Field(default=None, alias="failedStage")
    error_message: Optional[str] = Field(default=None, alias="errorMessage")
    target_langs: List[Languages] = Field(default_factory=list, alias="targetLangs")
    presets: Dict[str, str] = Field(default_factory=dict)

    class Config:
        allow_population_by_field_name = True
