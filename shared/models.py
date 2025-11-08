from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlmodel import Column, DateTime, Field, JSON, SQLModel


class JobStage(str, enum.Enum):
    INGESTED = "INGESTED"
    ASR = "ASR"
    TRANSLATE = "TRANSLATE"
    TTS = "TTS"
    ALIGN_MIX = "ALIGN/MIX"
    PACKAGE = "PACKAGE"
    PUBLISHED = "PUBLISHED"
    DONE = "DONE"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    user_id: Optional[str] = Field(default=None, index=True)
    src_lang: Optional[str] = Field(default=None, index=True)
    target_langs: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    storage_keys: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    duration_sec: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    asset_id: int = Field(foreign_key="assets.id")
    stage: JobStage = Field(default=JobStage.INGESTED)
    status: JobStatus = Field(default=JobStatus.PENDING)
    progress: float = Field(default=0.0)
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    logs_key: Optional[str] = Field(default=None)
    failed_stage: Optional[JobStage] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    target_langs: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    presets: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class Segment(SQLModel, table=True):
    __tablename__ = "segments"

    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="assets.id", index=True)
    idx: int = Field(index=True)
    speaker_id: Optional[str] = Field(default=None, index=True)
    t0: float
    t1: float
    text_src: str
    text_tgt: Optional[str] = None
    wav_tgt_key: Optional[str] = None


__all__ = [
    "Asset",
    "Job",
    "JobStage",
    "JobStatus",
    "Segment",
]
