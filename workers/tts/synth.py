from __future__ import annotations

import logging
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

import numpy as np
import soundfile as sf

from ..config import get_settings

DEFAULT_SR = 48000
PIPER_MIN_TEMPO = 0.90
PIPER_MAX_TEMPO = 1.10

_log = logging.getLogger(__name__)
_settings = get_settings()

VOICE_ALIAS: Dict[str, Dict[str, str]] = {
    lang: {
        "default": voice,
        "neutral": voice,
        "male_deep": voice,
        "female_bright": voice,
        "elderly_male": voice,
        "elderly_female": voice,
    }
    for lang, voice in _settings.piper_voices.items()
}


def _tone(duration: float, freq: float = 220.0, sr: int = DEFAULT_SR) -> np.ndarray:
    samples = int(max(duration, 0.1) * sr)
    t = np.linspace(0, duration, samples, False)
    waveform = 0.2 * np.sin(2 * math.pi * freq * t)
    return waveform.astype(np.float32)


def _segments_duration(segment: dict) -> float:
    return max(0.1, float(segment["t1"]) - float(segment["t0"]))


def _resolve_voice(language: str, preset: str | None) -> tuple[Path, Path] | None:
    voice_map = VOICE_ALIAS.get(language, {})
    preset = preset or "default"
    voice_candidate = voice_map.get(preset) or _settings.piper_voices.get(language)

    if voice_candidate is None and preset in _settings.piper_voices:
        voice_candidate = _settings.piper_voices[preset]

    if voice_candidate is None:
        return None

    model_path = Path(_settings.piper_model_dir) / voice_candidate
    config_path = model_path.parent / f"{model_path.name}.json"
    if not model_path.exists() or not config_path.exists():
        _log.warning(
            "Piper voice files missing for %s (%s). Expected model=%s config=%s",
            language,
            preset,
            model_path,
            config_path,
        )
        return None

    return model_path, config_path


def _synthesize_with_piper(text: str, model_path: Path, config_path: Path, output_path: Path, length_scale: float | None) -> None:
    cmd = [
        "piper",
        "--model",
        str(model_path),
        "--config",
        str(config_path),
        "--output_file",
        str(output_path),
    ]
    if length_scale is not None and 0.5 <= length_scale <= 2.0:
        cmd.extend(["--length_scale", f"{length_scale:.3f}"])

    try:
        subprocess.run(cmd, input=text.encode("utf-8"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise RuntimeError("piper CLI not found; ensure piper-tts is installed") from exc


def _render_with_ffmpeg(source: Path, destination: Path, tempo: float | None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", str(source), "-ac", "1", "-ar", str(DEFAULT_SR)]
    filters: List[str] = []
    if tempo and PIPER_MIN_TEMPO <= tempo <= PIPER_MAX_TEMPO and abs(tempo - 1.0) > 0.01:
        filters.append(f"atempo={tempo:.3f}")
    if filters:
        cmd.extend(["-filter:a", ",".join(filters)])
    cmd.append(str(destination))
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not available; required for resampling") from exc


def _write_fallback(segment: dict, output_path: Path, preset: str | None) -> None:
    duration = _segments_duration(segment)
    freq = 180.0
    if preset == "female_bright":
        freq = 260.0
    elif preset == "elderly_male":
        freq = 160.0
    waveform = _tone(duration, freq=freq)
    sf.write(output_path, waveform, DEFAULT_SR)


def synthesize_segments(
    translated_segments: List[dict],
    output_dir: Path,
    target_language: str,
    voice_presets: Dict[str, str] | None = None,
) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    voice_presets = voice_presets or {}
    generated_paths: List[Path] = []

    for segment in translated_segments:
        speaker_id = segment.get("speakerId") or "default"
        preset_key = voice_presets.get(speaker_id) or voice_presets.get("default") or speaker_id
        voice_choice = _resolve_voice(target_language, preset_key)
        final_path = output_dir / f"seg_{segment['idx']:04d}.wav"

        if voice_choice is None:
            _log.warning("Falling back to synthetic tone for segment %s", segment["idx"])
            _write_fallback(segment, final_path, preset_key)
            generated_paths.append(final_path)
            continue

        model_path, config_path = voice_choice
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            target_duration = _segments_duration(segment)
            length_scale = None
            if preset_key in {"elderly_male", "elderly_female"}:
                length_scale = 1.15
            elif preset_key == "female_bright":
                length_scale = 0.95

            text = segment.get("text_tgt") or segment.get("text_src") or ""
            _synthesize_with_piper(text, model_path, config_path, tmp_path, length_scale)
            info = sf.info(tmp_path.as_posix())
            current_duration = info.frames / info.samplerate if info.samplerate else target_duration
            tempo = target_duration / current_duration if current_duration else None
            if tempo is not None:
                tempo = max(PIPER_MIN_TEMPO, min(PIPER_MAX_TEMPO, tempo))
            _render_with_ffmpeg(tmp_path, final_path, tempo)
        except Exception as exc:  # pragma: no cover - dependent on external binaries
            _log.warning("Piper synthesis failed (%s); using fallback tone", exc)
            _write_fallback(segment, final_path, preset_key)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        generated_paths.append(final_path)

    return generated_paths
