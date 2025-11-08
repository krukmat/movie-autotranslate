from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .paths import (
    asr_segments_path,
    mix_output_file,
    tts_segment_path,
    translation_segments_path,
)


def has_asr_segments(asset_external_id: str) -> bool:
    return asr_segments_path(asset_external_id).exists()


def missing_translations(asset_external_id: str, languages: Iterable[str]) -> list[str]:
    missing = []
    for lang in languages:
        if not translation_segments_path(asset_external_id, lang).exists():
            missing.append(lang)
    return missing


def missing_tts_segments(asset_external_id: str, languages: Iterable[str]) -> list[str]:
    missing = []
    for lang in languages:
        lang_dir = tts_segment_path(asset_external_id, lang)
        if not lang_dir.exists() or not any(lang_dir.glob("seg_*.wav")):
            missing.append(lang)
    return missing


def missing_mixes(asset_external_id: str, languages: Iterable[str]) -> list[str]:
    missing = []
    for lang in languages:
        if not mix_output_file(asset_external_id, lang).exists():
            missing.append(lang)
    return missing
