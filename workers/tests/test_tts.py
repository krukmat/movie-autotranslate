from pathlib import Path

from workers.tts.synth import synthesize_segments


def test_synthesize_segments(tmp_path: Path) -> None:
    segments = [
        {"idx": 0, "t0": 0.0, "t1": 1.0, "text_tgt": "Hola"},
        {"idx": 1, "t0": 1.0, "t1": 2.0, "text_tgt": "Mundo"},
    ]
    generated = synthesize_segments(segments, tmp_path, target_language="es", voice_presets={"default": "female_bright"})
    assert len(generated) == 2
    for path in generated:
        assert path.exists()
        assert path.stat().st_size > 0
