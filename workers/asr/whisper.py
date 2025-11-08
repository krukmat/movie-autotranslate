from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_fixed

from ..config import get_settings

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - optional dependency
    WhisperModel = None  # type: ignore

_log = logging.getLogger(__name__)
_settings = get_settings()
_model_cache: dict[str, WhisperModel] = {}


def _load_model(model_size: str) -> WhisperModel | None:
    if WhisperModel is None:
        _log.warning("faster-whisper not installed; falling back to stub ASR output")
        return None
    cache_key = f"{model_size}:{_settings.asr_device}:{_settings.asr_compute_type}"
    if cache_key not in _model_cache:
        _log.info("Loading Whisper model %s on %s (%s)", model_size, _settings.asr_device, _settings.asr_compute_type)
        _model_cache[cache_key] = WhisperModel(
            model_size,
            device=_settings.asr_device,
            compute_type=_settings.asr_compute_type,
            download_root=_settings.asr_model_dir,
        )
    return _model_cache[cache_key]


def _assign_speaker(diarization: List[dict], t0: float, t1: float) -> Optional[str]:
    best_id: Optional[str] = None
    best_overlap = 0.0
    for entry in diarization:
        start = float(entry.get("t0", 0.0))
        end = float(entry.get("t1", 0.0))
        overlap = max(0.0, min(t1, end) - max(t0, start))
        if overlap > best_overlap:
            best_overlap = overlap
            best_id = entry.get("speaker") or entry.get("speakerId")
    return best_id


def _stub_segment() -> List[dict]:
    return [
        {
            "idx": 0,
            "t0": 0.0,
            "t1": 5.0,
            "text": "Sample transcription placeholder.",
            "lang": "en",
            "speakerId": "S0",
        }
    ]


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def transcribe(
    audio_path: Path,
    output_dir: Path,
    diarization: Optional[List[dict]] = None,
) -> List[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not audio_path.exists():
        _log.error("Audio path %s not found; returning stub segments", audio_path)
        segments = _stub_segment()
    else:
        model = _load_model(_settings.default_asr_model)
        if model is None:
            segments = _stub_segment()
        else:  # pragma: no cover - depends on external model weights
            segments_iter, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=True,
                language=None,
                task="transcribe",
            )
            detected_language = getattr(info, "language", "")
            diarization_data = diarization or []
            segments = []
            for idx, segment in enumerate(segments_iter):
                start = float(segment.start or 0.0)
                end = float(segment.end or 0.0)
                speaker_id = _assign_speaker(diarization_data, start, end) if diarization_data else None
                segments.append(
                    {
                        "idx": idx,
                        "t0": start,
                        "t1": end,
                        "text": segment.text.strip(),
                        "lang": segment.language or detected_language,
                        "speakerId": speaker_id,
                    }
                )

    output_path = output_dir / "segments_src.json"
    output_path.write_text(json.dumps(segments, indent=2), encoding="utf-8")
    return segments
