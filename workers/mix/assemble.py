from __future__ import annotations

import json
import logging
import math
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

from ..config import get_settings
from ..common import storage

DEFAULT_SR = 48_000

_log = logging.getLogger(__name__)
_settings = get_settings()


def _load_mono(path: Path) -> Tuple[np.ndarray, int]:
    data, sr = sf.read(path, always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data.astype(np.float32), sr


def _resample(audio: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return audio.astype(np.float32)
    gcd = math.gcd(src_sr, dst_sr)
    up = dst_sr // gcd
    down = src_sr // gcd
    resampled = signal.resample_poly(audio, up, down).astype(np.float32)
    return resampled


def _pad_to(array: np.ndarray, length: int) -> np.ndarray:
    if len(array) >= length:
        return array[:length]
    padding = length - len(array)
    return np.pad(array, (0, padding), mode="constant")


def _normalize_loudness(audio: np.ndarray, sample_rate: int, target_lufs: float) -> np.ndarray:
    if not np.any(audio):
        return audio
    meter = pyln.Meter(sample_rate)
    loudness = meter.integrated_loudness(audio)
    if math.isinf(loudness):
        return audio
    gain = target_lufs - loudness
    factor = 10 ** (gain / 20.0)
    normalized = audio * factor
    normalized = np.clip(normalized, -0.99, 0.99)
    return normalized.astype(np.float32)


def _voice_track(segments: List[dict], segment_paths: Iterable[Path]) -> Tuple[np.ndarray, int]:
    ordered = sorted(zip(segments, segment_paths), key=lambda item: item[0]["idx"])
    if not ordered:
        return np.zeros(DEFAULT_SR, dtype=np.float32), DEFAULT_SR

    max_t1 = max(float(seg["t1"]) for seg, _ in ordered)
    total_samples = max(DEFAULT_SR, int(math.ceil(max_t1 * DEFAULT_SR)) + DEFAULT_SR // 10)
    voice_track = np.zeros(total_samples, dtype=np.float32)

    for segment, path in ordered:
        audio, sr = _load_mono(path)
        audio = _resample(audio, sr, DEFAULT_SR)
        start = int(round(float(segment["t0"]) * DEFAULT_SR))
        end = start + len(audio)
        if end > len(voice_track):
            voice_track = _pad_to(voice_track, end)
        voice_track[start:end] += audio[: end - start]

    return voice_track, DEFAULT_SR


def _extract_background(source_audio: Path, sample_rate: int, work_dir: Path) -> np.ndarray:
    if not source_audio.exists():
        return np.zeros(sample_rate, dtype=np.float32)

    if _settings.mix_use_demucs:
        out_dir = work_dir / "demucs"
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            "demucs",
            "-n",
            _settings.demucs_model,
            "--two-stems=vocals",
            str(source_audio),
            "--out",
            str(out_dir),
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            background_candidate = next(out_dir.glob("**/no_vocals.wav"))
            background_audio, bg_sr = _load_mono(background_candidate)
            return _resample(background_audio, bg_sr, sample_rate)
        except (FileNotFoundError, StopIteration, subprocess.CalledProcessError) as exc:
            _log.warning("Demucs separation unavailable (%s); using attenuated source", exc)

    original_audio, original_sr = _load_mono(source_audio)
    return _resample(original_audio, original_sr, sample_rate)


def assemble_track(
    translated_segments: List[dict],
    segment_paths: List[Path],
    output_dir: Path,
    source_audio: Path | None,
    target_language: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    voice_track, sample_rate = _voice_track(translated_segments, segment_paths)
    background = np.zeros_like(voice_track)
    if source_audio:
        background = _extract_background(source_audio, sample_rate, output_dir)

    mix_length = max(len(voice_track), len(background))
    voice_track = _pad_to(voice_track, mix_length) * float(_settings.mix_voice_gain)
    background = _pad_to(background, mix_length) * float(_settings.mix_background_gain)

    mixed = voice_track + background
    mixed = _normalize_loudness(mixed, sample_rate, _settings.mix_target_loudness)
    mixed = np.nan_to_num(mixed, nan=0.0)

    voice_path = output_dir / f"voice_{target_language}.wav"
    background_path = output_dir / f"background_{target_language}.wav"
    sf.write(voice_path, voice_track, sample_rate)
    sf.write(background_path, background, sample_rate)

    final_path = output_dir / "dubbed.wav"
    sf.write(final_path, mixed, sample_rate)
    return final_path


def publish_track(asset_id: str, language: str, audio_path: Path, public_dir: Path) -> str:
    playlist_dir = public_dir / language
    playlist_dir.mkdir(parents=True, exist_ok=True)
    master_path = public_dir / "master.m3u8"
    audio_object_name = f"pub/{asset_id}/{language}/dubbed.wav"
    storage.upload_from_path(
        _settings.minio_bucket_public,
        audio_object_name,
        audio_path,
        content_type="audio/wav",
    )
    manifest = {
        "assetId": asset_id,
        "language": language,
        "audioObject": audio_object_name,
    }
    master_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    master_object_name = f"pub/{asset_id}/master.m3u8"
    try:
        storage.upload_from_path(
            _settings.minio_bucket_public,
            master_object_name,
            master_path,
            content_type="application/vnd.apple.mpegurl",
        )
        return master_object_name
    except Exception:  # pragma: no cover - depends on MinIO
        return master_path.as_posix()
