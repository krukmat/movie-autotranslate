from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - fallback for environments without Celery installed
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator
try:  # pragma: no cover - allow local tests without prometheus_client
    from prometheus_client import start_http_server
except ImportError:  # pragma: no cover
    def start_http_server(*_args, **_kwargs) -> None:
        return None


_TASK_RETRY_KWARGS = {
    "bind": True,
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
    "retry_kwargs": {"max_retries": 3},
}
from sqlmodel import select

from shared.models import Asset, Job, JobStage, JobStatus

from ..asr.whisper import transcribe
from ..common import artifacts
from ..common import assets as asset_state
from ..common import jobs as job_state
from ..common.db import get_session
from ..common.logging import (
    configure_stdout_logging,
    log_event,
    set_job_log_file,
    stage_context,
)
from ..common.paths import (
    asset_public_dir,
    asset_workspace,
    job_log_path,
    mix_output_file,
)
from ..common.storage import download_to_path, upload_from_path
from ..config import get_settings
from ..diarization.basic import run_diarization
from ..mix.assemble import assemble_track, publish_track
from ..mt.translate import translate_segments
from ..tts.synth import synthesize_segments

_settings = get_settings()
configure_stdout_logging()
try:  # pragma: no cover - metrics server optional
    start_http_server(_settings.metrics_port, addr=_settings.metrics_host)
except OSError:
    pass

STAGE_PROGRESS = {
    JobStage.ASR: 0.10,
    JobStage.TRANSLATE: 0.30,
    JobStage.TTS: 0.55,
    JobStage.ALIGN_MIX: 0.75,
    JobStage.PACKAGE: 0.90,
}

STAGE_ORDER = {
    JobStage.ASR: 1,
    JobStage.TRANSLATE: 2,
    JobStage.TTS: 3,
    JobStage.ALIGN_MIX: 4,
    JobStage.PACKAGE: 5,
    JobStage.DONE: 6,
}


def _load_job(job_external_id: str) -> tuple[Job, Asset]:
    with get_session() as session:
        job = session.exec(select(Job).where(Job.external_id == job_external_id)).one()
        asset = session.get(Asset, job.asset_id)
        if asset is None:
            raise RuntimeError("Asset missing for job")
        return job, asset


def _update_job(job_external_id: str, stage: JobStage, progress: float) -> None:
    job_state.update_job(job_external_id, stage=stage, status=JobStatus.RUNNING, progress=progress)


def _stage_order(stage: JobStage) -> int:
    return STAGE_ORDER.get(stage, 0)


def _should_skip(stage: JobStage, resume_stage: JobStage, artifact_ready: bool) -> bool:
    return _stage_order(stage) < _stage_order(resume_stage) and artifact_ready


def _retry_state(task: Any) -> tuple[int, bool]:
    request = getattr(task, "request", None)
    retries = getattr(request, "retries", 0) or 0
    max_retries = getattr(task, "max_retries", 0) or 0
    if not max_retries:
        retry_kwargs = getattr(task, "retry_kwargs", {}) or {}
        max_retries = retry_kwargs.get("max_retries", 0) or 0
    return int(retries), retries < max_retries if max_retries else False


def _target_languages(job: Job, asset: Asset) -> List[str]:
    langs = job.target_langs or asset.target_langs
    if not langs:
        return ["es"]
    return langs


def _parse_resume(stage_value: Optional[str]) -> JobStage:
    if not stage_value:
        return JobStage.ASR
    try:
        return JobStage(stage_value)
    except ValueError:
        return JobStage.ASR


def _ensure_source_audio(asset: Asset, workspace: Path) -> Path:
    audio_path = workspace / "source.wav"
    raw_key = asset.storage_keys.get("raw")
    if audio_path.exists():
        return audio_path
    if raw_key:
        download_to_path(_settings.minio_bucket_raw, raw_key, audio_path)
    if not audio_path.exists():
        audio_path.write_bytes(b"\x00\x00")
    return audio_path


def _missing_packages(asset: Asset, languages: List[str]) -> List[str]:
    missing = []
    storage_keys = asset.storage_keys or {}
    for lang in languages:
        if not storage_keys.get(f"public_{lang}"):
            missing.append(lang)
    return missing


def _persist_job_logs(job: Job, asset: Asset, log_path: Path) -> None:
    if not log_path.exists():
        job_state.update_logs_key(job.external_id, None)
        return
    object_name = f"proc/{asset.external_id}/logs/{job.external_id}.jsonl"
    try:
        from ..common.storage import upload_from_path

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
    log_path = job_log_path(asset.external_id, job.external_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    resume_value = (resume_from or JobStage.ASR.value)
    _update_job(job_id, JobStage.INGESTED, 0.01)
    set_job_log_file(log_path)
    log_event(
        job_id=job.external_id,
        asset_id=asset.external_id,
        stage="PIPELINE",
        event="START",
        message=f"Pipeline queued (resumeFrom={resume_value})",
    )
    set_job_log_file(None)
    run_asr_stage.delay(job_id, resume_value, str(log_path))
    return job_id


@shared_task(name="workers.pipeline.run_asr_stage", **_TASK_RETRY_KWARGS)
def run_asr_stage(self, job_id: str, resume_from: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    workspace = asset_workspace(asset.external_id)
    audio_path = _ensure_source_audio(asset, workspace)
    resume_stage = _parse_resume(resume_from)
    artifact_ready = artifacts.has_asr_segments(asset.external_id)
    _update_job(job_id, JobStage.ASR, STAGE_PROGRESS[JobStage.ASR])

    if _should_skip(JobStage.ASR, resume_stage, artifact_ready):
        job_state.record_stage_history(job_id, JobStage.ASR.value, "skipped")
        log_event(job_id=job_id, asset_id=asset.external_id, stage=JobStage.ASR.value, event="SKIP", message="ASR skipped (resume)")
    else:
        diarization_segments = None
        diarization_dir = workspace / "diarization"
        diarization_enabled = bool(asset.storage_keys.get("diarization"))
        timer = None
        try:
            with stage_context(job_id=job_id, asset_id=asset.external_id, stage=JobStage.ASR.value) as stage_timer:
                timer = stage_timer
                if diarization_enabled:
                    diarization_segments = run_diarization(audio_path, diarization_dir)
                asr_dir = workspace / "asr"
                transcribe(audio_path, asr_dir, diarization_segments)
            details = {"diarization": diarization_enabled}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            job_state.record_stage_history(job_id, JobStage.ASR.value, "success", details)
        except Exception as exc:
            retries, will_retry = _retry_state(self)
            attempt = retries + 1
            details = {"error": str(exc), "attempt": attempt}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            status = "retrying" if will_retry else "failed"
            job_state.record_stage_history(job_id, JobStage.ASR.value, status, details)
            set_job_log_file(None)
            if will_retry:
                log_event(
                    job_id=job_id,
                    asset_id=asset.external_id,
                    stage=JobStage.ASR.value,
                    event="RETRY",
                    message=f"ASR failed (attempt {attempt}), retrying",
                )
                raise
            job_state.mark_failure(job_id, JobStage.ASR, str(exc))
            raise

    set_job_log_file(None)
    run_translate_stage.delay(job_id, resume_from, log_file)


@shared_task(name="workers.pipeline.run_translate_stage", **_TASK_RETRY_KWARGS)
def run_translate_stage(self, job_id: str, resume_from: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    resume_stage = _parse_resume(resume_from)
    workspace = asset_workspace(asset.external_id)
    asr_path = workspace / "asr" / "segments_src.json"
    if not asr_path.exists():
        job_state.mark_failure(job_id, JobStage.TRANSLATE, "Missing ASR output")
        set_job_log_file(None)
        raise RuntimeError("ASR output missing; cannot translate")

    languages = _target_languages(job, asset)
    missing = artifacts.missing_translations(asset.external_id, languages)
    artifact_ready = len(missing) == 0
    _update_job(job_id, JobStage.TRANSLATE, STAGE_PROGRESS[JobStage.TRANSLATE])

    if _should_skip(JobStage.TRANSLATE, resume_stage, artifact_ready):
        job_state.record_stage_history(job_id, JobStage.TRANSLATE.value, "skipped", {"languages": languages})
        log_event(job_id=job_id, asset_id=asset.external_id, stage=JobStage.TRANSLATE.value, event="SKIP", message="Translations reused")
    else:
        lang_status: Dict[str, str] = {lang: "existing" for lang in languages if lang not in missing}
        timer = None
        try:
            with stage_context(
                job_id=job_id,
                asset_id=asset.external_id,
                stage=JobStage.TRANSLATE.value,
                metadata={"targets": languages},
            ) as stage_timer:
                timer = stage_timer
                translations_dir = workspace / "translations"
                for lang in languages:
                    if lang in missing:
                        translate_segments(asr_path, translations_dir, lang)
                        lang_status[lang] = "success"
            details = {"languages": lang_status}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            job_state.record_stage_history(job_id, JobStage.TRANSLATE.value, "success", details)
        except Exception as exc:
            retries, will_retry = _retry_state(self)
            attempt = retries + 1
            details = {"error": str(exc), "attempt": attempt}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            status = "retrying" if will_retry else "failed"
            job_state.record_stage_history(job_id, JobStage.TRANSLATE.value, status, details)
            set_job_log_file(None)
            if will_retry:
                log_event(
                    job_id=job_id,
                    asset_id=asset.external_id,
                    stage=JobStage.TRANSLATE.value,
                    event="RETRY",
                    message=f"Translation failed (attempt {attempt}), retrying",
                )
                raise
            job_state.mark_failure(job_id, JobStage.TRANSLATE, str(exc))
            raise

    set_job_log_file(None)
    run_tts_stage.delay(job_id, resume_from, log_file)


@shared_task(name="workers.pipeline.run_tts_stage", **_TASK_RETRY_KWARGS)
def run_tts_stage(self, job_id: str, resume_from: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    resume_stage = _parse_resume(resume_from)
    languages = _target_languages(job, asset)
    missing = artifacts.missing_tts_segments(asset.external_id, languages)
    artifact_ready = len(missing) == 0
    _update_job(job_id, JobStage.TTS, STAGE_PROGRESS[JobStage.TTS])

    if _should_skip(JobStage.TTS, resume_stage, artifact_ready):
        job_state.record_stage_history(job_id, JobStage.TTS.value, "skipped", {"languages": languages})
        log_event(job_id=job_id, asset_id=asset.external_id, stage=JobStage.TTS.value, event="SKIP", message="TTS reused")
    else:
        workspace = asset_workspace(asset.external_id)
        translations_dir = workspace / "translations"
        lang_status: Dict[str, str] = {lang: "existing" for lang in languages if lang not in missing}
        timer = None
        try:
            with stage_context(
                job_id=job_id,
                asset_id=asset.external_id,
                stage=JobStage.TTS.value,
                metadata={"targets": languages},
            ) as stage_timer:
                timer = stage_timer
                for lang in languages:
                    segments_path = translations_dir / f"segments_tgt.{lang}.json"
                    translated_segments = json.loads(segments_path.read_text(encoding="utf-8"))
                    if lang in missing:
                        synthesize_segments(
                            translated_segments,
                            workspace / "tts" / lang,
                            target_language=lang,
                            voice_presets=job.presets,
                        )
                        lang_status[lang] = "success"
            details = {"languages": lang_status}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            job_state.record_stage_history(job_id, JobStage.TTS.value, "success", details)
        except Exception as exc:
            retries, will_retry = _retry_state(self)
            attempt = retries + 1
            details = {"error": str(exc), "attempt": attempt}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            status = "retrying" if will_retry else "failed"
            job_state.record_stage_history(job_id, JobStage.TTS.value, status, details)
            set_job_log_file(None)
            if will_retry:
                log_event(
                    job_id=job_id,
                    asset_id=asset.external_id,
                    stage=JobStage.TTS.value,
                    event="RETRY",
                    message=f"TTS failed (attempt {attempt}), retrying",
                )
                raise
            job_state.mark_failure(job_id, JobStage.TTS, str(exc))
            raise

    set_job_log_file(None)
    run_mix_stage.delay(job_id, resume_from, log_file)


@shared_task(name="workers.pipeline.run_mix_stage", **_TASK_RETRY_KWARGS)
def run_mix_stage(self, job_id: str, resume_from: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    resume_stage = _parse_resume(resume_from)
    languages = _target_languages(job, asset)
    missing = artifacts.missing_mixes(asset.external_id, languages)
    artifact_ready = len(missing) == 0
    _update_job(job_id, JobStage.ALIGN_MIX, STAGE_PROGRESS[JobStage.ALIGN_MIX])

    workspace = asset_workspace(asset.external_id)
    audio_path = _ensure_source_audio(asset, workspace)

    if _should_skip(JobStage.ALIGN_MIX, resume_stage, artifact_ready):
        job_state.record_stage_history(job_id, JobStage.ALIGN_MIX.value, "skipped", {"languages": languages})
        log_event(job_id=job_id, asset_id=asset.external_id, stage=JobStage.ALIGN_MIX.value, event="SKIP", message="Mix reused")
    else:
        lang_status: Dict[str, str] = {lang: "existing" for lang in languages if lang not in missing}
        timer = None
        try:
            with stage_context(
                job_id=job_id,
                asset_id=asset.external_id,
                stage=JobStage.ALIGN_MIX.value,
                metadata={"targets": languages},
            ) as stage_timer:
                timer = stage_timer
                for lang in languages:
                    segments_path = workspace / "translations" / f"segments_tgt.{lang}.json"
                    translated_segments = json.loads(segments_path.read_text(encoding="utf-8"))
                    tts_dir = workspace / "tts" / lang
                    synth_paths = sorted(tts_dir.glob("seg_*.wav"))
                    if lang in missing:
                        final_audio = assemble_track(
                            translated_segments,
                            synth_paths,
                            workspace / "mix" / lang,
                            source_audio=audio_path,
                            target_language=lang,
                        )
                        if not final_audio.exists():
                            raise RuntimeError(f"Mix failed for {lang}")
                        lang_status[lang] = "success"
            details = {"languages": lang_status}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            job_state.record_stage_history(job_id, JobStage.ALIGN_MIX.value, "success", details)
        except Exception as exc:
            retries, will_retry = _retry_state(self)
            attempt = retries + 1
            details = {"error": str(exc), "attempt": attempt}
            if timer and timer.duration_ms is not None:
                details["durationMs"] = timer.duration_ms
            status = "retrying" if will_retry else "failed"
            job_state.record_stage_history(job_id, JobStage.ALIGN_MIX.value, status, details)
            set_job_log_file(None)
            if will_retry:
                log_event(
                    job_id=job_id,
                    asset_id=asset.external_id,
                    stage=JobStage.ALIGN_MIX.value,
                    event="RETRY",
                    message=f"Mix failed (attempt {attempt}), retrying",
                )
                raise
            job_state.mark_failure(job_id, JobStage.ALIGN_MIX, str(exc))
            raise

    set_job_log_file(None)
    run_package_stage.delay(job_id, resume_from, log_file)


@shared_task(name="workers.pipeline.run_package_stage", **_TASK_RETRY_KWARGS)
def run_package_stage(self, job_id: str, resume_from: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    resume_stage = _parse_resume(resume_from)
    languages = _target_languages(job, asset)
    missing = _missing_packages(asset, languages)
    artifact_ready = len(missing) == 0
    _update_job(job_id, JobStage.PACKAGE, STAGE_PROGRESS[JobStage.PACKAGE])

    storage_keys = asset.storage_keys or {}
    asset.storage_keys = storage_keys

    if _should_skip(JobStage.PACKAGE, resume_stage, artifact_ready):
        job_state.record_stage_history(job_id, JobStage.PACKAGE.value, "skipped", {"languages": languages})
        log_event(job_id=job_id, asset_id=asset.external_id, stage=JobStage.PACKAGE.value, event="SKIP", message="Package reused")
        set_job_log_file(None)
        finalize_job.delay(job_id, log_file)
        return

    lang_status: Dict[str, str] = {lang: "existing" for lang in languages if lang not in missing}
    public_dir = asset_public_dir(asset.external_id)
    timer = None
    try:
        with stage_context(
            job_id=job_id,
            asset_id=asset.external_id,
            stage=JobStage.PACKAGE.value,
            metadata={"targets": languages},
        ) as stage_timer:
            timer = stage_timer
            for lang in languages:
                mix_path = mix_output_file(asset.external_id, lang)
                if not mix_path.exists():
                    raise RuntimeError(f"Missing mix output for {lang}")
                if lang in missing:
                    publish_info = publish_track(asset.external_id, lang, mix_path, public_dir)
                    master_key = publish_info["master"]
                    audio_key = publish_info["audio"]
                    if "public" not in asset.storage_keys:
                        asset.storage_keys["public"] = master_key
                    asset.storage_keys[f"public_{lang}"] = audio_key
                    asset_state.update_storage_keys(asset.external_id, asset.storage_keys)
                    lang_status[lang] = "success"
        details = {"languages": lang_status}
        if timer and timer.duration_ms is not None:
            details["durationMs"] = timer.duration_ms
        job_state.record_stage_history(job_id, JobStage.PACKAGE.value, "success", details)
    except Exception as exc:
        retries, will_retry = _retry_state(self)
        attempt = retries + 1
        details = {"error": str(exc), "attempt": attempt}
        if timer and timer.duration_ms is not None:
            details["durationMs"] = timer.duration_ms
        status = "retrying" if will_retry else "failed"
        job_state.record_stage_history(job_id, JobStage.PACKAGE.value, status, details)
        set_job_log_file(None)
        if will_retry:
            log_event(
                job_id=job_id,
                asset_id=asset.external_id,
                stage=JobStage.PACKAGE.value,
                event="RETRY",
                message=f"Packaging failed (attempt {attempt}), retrying",
            )
            raise
        job_state.mark_failure(job_id, JobStage.PACKAGE, str(exc))
        raise

    set_job_log_file(None)
    finalize_job.delay(job_id, log_file)


@shared_task(name="workers.pipeline.finalize_job")
def finalize_job(job_id: str, log_file: str) -> None:
    set_job_log_file(Path(log_file))
    job, asset = _load_job(job_id)
    log_event(job_id=job_id, asset_id=asset.external_id, stage="PIPELINE", event="END", message="Pipeline finished")
    _persist_job_logs(job, asset, Path(log_file))
    job_state.mark_success(job_id)
    set_job_log_file(None)
