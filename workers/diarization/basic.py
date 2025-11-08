from __future__ import annotations

import json
from pathlib import Path
from typing import List


def run_diarization(audio_path: Path, output_dir: Path) -> List[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Placeholder diarization: single speaker assumption.
    segments = [{"idx": 0, "speaker": "S0", "t0": 0.0, "t1": 5.0}]
    (output_dir / "speakers.json").write_text(json.dumps(segments, indent=2), encoding="utf-8")
    return segments
