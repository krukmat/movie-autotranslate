"""Seed script that creates a placeholder asset and job for local demos.

Run after `make up` once the stack is healthy. The script uploads a small
synthetic WAV file so the pipeline can run end-to-end without external media.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path

import requests

API_BASE = "http://localhost:8000/v1"


def _generate_wav(duration: float = 2.0, sample_rate: int = 16000) -> bytes:
    import math
    import struct

    frame_count = int(duration * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for n in range(frame_count):
            value = int(32767 * math.sin(2 * math.pi * 220 * (n / sample_rate)))
            wav.writeframes(struct.pack("<h", value))
    return buffer.getvalue()


def seed_demo() -> None:
    demo_audio = _generate_wav()
    payload = {
        "filename": "demo.wav",
        "contentType": "audio/wav",
        "size": len(demo_audio),
    }
    response = requests.post(f"{API_BASE}/upload/init", json=payload, timeout=10)
    response.raise_for_status()
    init_data = response.json()

    upload_url = init_data["parts"][0]["uploadUrl"]
    upload_headers = {"Content-Type": "audio/wav"}
    upload_resp = requests.put(upload_url, data=demo_audio, headers=upload_headers, timeout=10)
    upload_resp.raise_for_status()

    complete_payload = {
        "assetId": init_data["assetId"],
        "uploadId": init_data["uploadId"],
        "etags": [upload_resp.headers.get("ETag", "demo-etag")],
        "srcLang": "en",
        "targetLangs": ["es"],
    }
    requests.post(f"{API_BASE}/upload/complete", json=complete_payload, timeout=10).raise_for_status()

    job_payload = {
        "assetId": init_data["assetId"],
        "targetLangs": ["es"],
        "presets": {"default": "male_deep"},
    }
    job_resp = requests.post(f"{API_BASE}/jobs/translate", json=job_payload, timeout=10)
    job_resp.raise_for_status()
    job_data = job_resp.json()
    print("Seeded demo job", job_data)


if __name__ == "__main__":
    try:
        seed_demo()
    except requests.RequestException as exc:
        print("Could not seed demo job. Ensure the API and MinIO are running.")
        print(f"Error: {exc}")
