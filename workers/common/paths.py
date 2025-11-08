from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROC_DIR = DATA_DIR / "proc"
RAW_DIR = DATA_DIR / "raw"
PUB_DIR = DATA_DIR / "pub"


def asset_workspace(asset_external_id: str) -> Path:
    path = PROC_DIR / asset_external_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def asset_public_dir(asset_external_id: str) -> Path:
    path = PUB_DIR / asset_external_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def asr_segments_path(asset_external_id: str) -> Path:
    return asset_workspace(asset_external_id) / "asr" / "segments_src.json"


def translation_segments_path(asset_external_id: str, language: str) -> Path:
    return asset_workspace(asset_external_id) / "translations" / f"segments_tgt.{language}.json"


def tts_segment_path(asset_external_id: str, language: str) -> Path:
    return asset_workspace(asset_external_id) / "tts" / language


def mix_output_dir(asset_external_id: str, language: str) -> Path:
    return asset_workspace(asset_external_id) / "mix" / language


def mix_output_file(asset_external_id: str, language: str) -> Path:
    return mix_output_dir(asset_external_id, language) / "dubbed.wav"


def job_log_path(asset_external_id: str, job_external_id: str) -> Path:
    return asset_workspace(asset_external_id) / "logs" / f"{job_external_id}.jsonl"
