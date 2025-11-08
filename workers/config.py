from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import BaseSettings, Field


def _default_database_url() -> str:
    root = Path(__file__).resolve().parents[1]
    return f"sqlite:///{root / 'data' / 'app.db'}"


def _default_piper_voices() -> Dict[str, str]:
    return {
        "en": "en/en_US-amy-medium.onnx",
        "es": "es/es_ES-ana-medium.onnx",
        "fr": "fr/fr_FR-arthur-medium.onnx",
        "de": "de/de_DE-thorsten-medium.onnx",
    }


class WorkerSettings(BaseSettings):
    redis_url: str = Field(default="redis://redis:6379/0", env="REDIS_URL")
    broker_queue: str = Field(default="pipeline", env="BROKER_QUEUE")
    database_url: str = Field(default_factory=_default_database_url, env="DATABASE_URL")
    minio_endpoint: str = Field(default="minio:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket_raw: str = Field(default="raw", env="MINIO_BUCKET_RAW")
    minio_bucket_processed: str = Field(default="proc", env="MINIO_BUCKET_PROCESSED")
    minio_bucket_public: str = Field(default="pub", env="MINIO_BUCKET_PUBLIC")

    default_asr_model: str = Field(default="small", env="ASR_MODEL")
    asr_device: str = Field(default="cpu", env="ASR_DEVICE")
    asr_compute_type: str = Field(default="int8", env="ASR_COMPUTE_TYPE")
    asr_model_dir: str = Field(default=str(Path.home() / ".cache" / "faster-whisper"), env="ASR_MODEL_DIR")

    allowed_languages: List[str] = Field(default_factory=lambda: ["en", "es", "fr", "de"])
    libretranslate_url: str = Field(default="http://libretranslate:5000", env="LIBRETRANSLATE_URL")

    tts_engine: str = Field(default="piper", env="TTS_ENGINE")
    piper_model_dir: str = Field(default=str(Path.home() / ".cache" / "piper"), env="PIPER_MODEL_DIR")
    piper_voices: Dict[str, str] = Field(default_factory=_default_piper_voices, env="PIPER_VOICES")

    mix_use_demucs: bool = Field(default=False, env="MIX_USE_DEMUCS")
    demucs_model: str = Field(default="htdemucs", env="DEMUCS_MODEL")
    demucs_output_dir: str = Field(default=str(Path.home() / ".cache" / "demucs"), env="DEMUCS_OUTPUT_DIR")
    mix_voice_gain: float = Field(default=1.0, env="MIX_VOICE_GAIN")
    mix_background_gain: float = Field(default=0.35, env="MIX_BACKGROUND_GAIN")
    mix_target_loudness: float = Field(default=-16.0, env="MIX_TARGET_LOUDNESS")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
