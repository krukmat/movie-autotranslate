from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from libretranslatepy import LibreTranslateAPI
from tenacity import retry, stop_after_attempt, wait_fixed

from ..config import get_settings

_settings = get_settings()


def _apply_glossary(text: str, glossary: Dict[str, str]) -> str:
    for src, dst in glossary.items():
        text = text.replace(src, dst)
    return text


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def translate_segments(
    segments_src_path: Path,
    output_dir: Path,
    target_lang: str,
    glossary: Dict[str, str] | None = None,
) -> List[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    segments = json.loads(segments_src_path.read_text(encoding="utf-8"))
    glossary = glossary or {}

    try:
        client = LibreTranslateAPI(_settings.libretranslate_url)
    except Exception:  # pragma: no cover - network dependency
        client = None  # type: ignore

    translated: List[dict] = []
    for segment in segments:
        text_src = _apply_glossary(segment["text"], glossary)
        if client is None:
            text_tgt = text_src  # fallback to source text
        else:  # pragma: no cover - requires LibreTranslate service
            text_tgt = client.translate(text_src, segment.get("lang", "auto"), target_lang)
        translated.append(
            {
                "idx": segment["idx"],
                "t0": segment["t0"],
                "t1": segment["t1"],
                "text_src": segment["text"],
                "text_tgt": text_tgt,
                "speakerId": segment.get("speakerId"),
            }
        )

    output_path = output_dir / f"segments_tgt.{target_lang}.json"
    output_path.write_text(json.dumps(translated, indent=2), encoding="utf-8")
    return translated
