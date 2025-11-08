from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from workers.mix.assemble import assemble_track


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int = 48_000) -> None:
    sf.write(path, samples.astype(np.float32), sample_rate)


def test_assemble_track_normalizes_and_aligns(tmp_path: Path) -> None:
    sample_rate = 48_000
    duration_seconds = 2.0
    total_samples = int(sample_rate * duration_seconds)
    # Original audio: low-amplitude ambient noise
    original_audio = 0.05 * np.random.default_rng(0).standard_normal(total_samples).astype(np.float32)
    original_path = tmp_path / "original.wav"
    _write_wav(original_path, original_audio, sample_rate)

    # Two synthesized segments covering the full duration
    segments = [
        {"idx": 0, "t0": 0.0, "t1": 1.0, "text_tgt": "Hola"},
        {"idx": 1, "t0": 1.0, "t1": 2.0, "text_tgt": "Mundo"},
    ]
    seg_paths = []
    tone = 0.2 * np.sin(2 * np.pi * np.linspace(0, 1.0, sample_rate, endpoint=False))
    for segment in segments:
        path = tmp_path / f"seg_{segment['idx']:04d}.wav"
        _write_wav(path, tone, sample_rate)
        seg_paths.append(path)

    output_dir = tmp_path / "mix"
    final_path = assemble_track(segments, seg_paths, output_dir, original_path, target_language="es")
    assert final_path.exists()

    mixed_audio, sr = sf.read(final_path)
    assert sr == sample_rate
    assert len(mixed_audio) >= total_samples
    meter = pyln.Meter(sample_rate)
    loudness = meter.integrated_loudness(mixed_audio)
    assert -18.5 < loudness < -13.5
