from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from celery import shared_task
from prometheus_client import start_http_server
from sqlmodel import select

from shared.models import Asset, Job, JobStage, JobStatus

from ..asr.whisper import transcribe
from ..common import assets as asset_state
from ..common import jobs as job_state
from ..common.db import get_session
from ..common.logging import (
    configure_stdout_logging,
    log_event,
    set_job_log_file,
    stage_context,
)
from ..common.paths import asset_public_dir, asset_workspace
from ..common.storage import download_to_path, upload_from_path
from ..config import get_settings
from ..diarization.basic import run_diarization
from ..mix.assemble import assemble_track, publish_track
from ..mt.translate import translate_segments
from ..tts.synth import synthesize_segments

_settings = get_settings()
configure_stdout_logging()
try:  # pragma: no cover
    start_http_server(_settings.metrics_port, addr=_settings.metrics_host)
except OSError:
    pass


def _load_job(job_external_id: str) -> tuple[Job, Asset]:
    with get_session() as session:
        job = session.exec(select(Job).where(Job.external_id == job_external_id)).one()
        asset = session.get(Asset, job.asset_id)
        if asset is None:
            raise RuntimeError("Asset missing for job")
        return job, asset


def _update_job(job_external_id: str, stage: JobStage, progress: float) -> None:
    job_state.update_job(job_external_id, stage=stage, status=JobStatus.RUNNING, progress=progress)


def _persist_job_logs(job: Job, asset: Asset, log_path: Path) -> None:
    if not log_path.exists():
        job_state.update_logs_key(job.external_id, None)
        return
    object_name = f"proc/{asset.external_id}/logs/{job.external_id}.jsonl"
    try:
        upload_from_path(
            _settings.minio_bucket_processed,
            object_name,
            log_path,
            content_type="application/json",
        )
        job_state.update_logs_key(job.external_id, object_name)
    except Exception as exc:  # pragma: no cover
        log_event(
            job_id=job.external_id,
            asset_id=asset.external_id,
            stage="LOG_UPLOAD",
            event="ERROR",
            message="Failed to upload job logs",
            extra={"error": str(exc)},
        )
@shared_task(name="workers.pipeline.run_pipeline")
def run_pipeline(job_id: str, resume_from: Optional[str] = None) -> str:
    job, asset = _load_job(job_id)
    workspace = asset_workspace(asset.external_id)
    current_stage = JobStage.INGESTED
    log_path = workspace / "logs" / f"{job.external_id}.jsonl"
    set_job_log_file(log_path)

    try:
        raw_key = asset.storage_keys.get("raw")
        audio_path = workspace / "source.wav"
        try:
            if raw_key:
                download_to_path(_settings.minio_bucket_raw, raw_key, audio_path)
            if not audio_path.exists():
                audio_path.write_bytes(b"\x00\x00")
        except Exception as exc:  # pragma: no cover - network services optional
            log_event(
                job_id=job_id,
                asset_id=asset.external_id,
                stage="FETCH_SOURCE",
                event="WARN",
                message="Falling back to blank audio",
                extra={"error": str(exc)},
            )
            audio_path.write_bytes(b"\x00\x00")

        diarization_segments = None
        # Stage: ASR
        current_stage = JobStage.ASR
        _update_job(job_id, JobStage.ASR, 0.05)
        diarization_dir = workspace / "diarization"
        diarization_enabled = bool(asset.storage_keys.get("diarization"))
        with stage_context(job_id=job_id, asset_id=asset.external_id, stage="ASR"):
            if diarization_enabled:
                diarization_segments = run_diarization(audio_path, diarization_dir)
            asr_dir = workspace / "asr"
            transcribe(audio_path, asr_dir, diarization_segments)

        # Stage: TRANSLATE
        current_stage = JobStage.TRANSLATE
        _update_job(job_id, JobStage.TRANSLATE, 0.25)
        translations_dir = workspace / "translations"
        target_languages = job.target_langs or asset.target_langs or ["es"]
        with stage_context(job_id=job_id, asset_id=asset.external_id, stage="TRANSLATE", metadata={"targets": target_languages}):
            for target_lang in target_languages:
                translate_segments(asr_dir / "segments_src.json", translations_dir, target_lang)

        # Stage: TTS & MIX for each language
        for target_lang in target_languages:
            current_stage = JobStage.TTS
            _update_job(job_id, JobStage.TTS, 0.45)
            tts_dir = workspace / "tts"
            with stage_context(job_id=job_id, asset_id=asset.external_id, stage=f"TTS_{target_lang}"):
                segments_path = translations_dir / f"segments_tgt.{target_lang}.json"
                translated_segments = json.loads(segments_path.read_text(encoding="utf-8"))
                synth_paths = synthesize_segments(
                    translated_segments,
                    tts_dir / target_lang,
                    target_language=target_lang,
                    voice_presets=job.presets,
                )

            current_stage = JobStage.ALIGN_MIX
            _update_job(job_id, JobStage.ALIGN_MIX, 0.65)
            mix_dir = workspace / "mix" / target_lang
            with stage_context(job_id=job_id, asset_id=asset.external_id, stage=f"MIX_{target_lang}"):
                final_audio = assemble_track(
                    translated_segments,
                    synth_paths,
                    mix_dir,
                    source_audio=audio_path,
                    target_language=target_lang,
                )

            current_stage = JobStage.PACKAGE
            _update_job(job_id, JobStage.PACKAGE, 0.8)
            with stage_context(job_id=job_id, asset_id=asset.external_id, stage=f"PACKAGE_{target_lang}"):
                public_dir = asset_public_dir(asset.external_id)
                public_object = publish_track(asset.external_id, target_lang, final_audio, public_dir)
                asset.storage_keys["public"] = public_object
                asset.storage_keys[f"public_{target_lang}"] = public_object
                asset_state.update_storage_keys(asset.external_id, asset.storage_keys)

        current_stage = JobStage.PUBLISHED
        _update_job(job_id, JobStage.PUBLISHED, 0.95)
        job_state.mark_success(job_id)
    except Exception as exc:  # pragma: no cover
        job_state.mark_failure(job_id, current_stage, str(exc))
        raise
    finally:
        _persist_job_logs(job, asset, log_path)
        set_job_log_file(None)

    return job_id
