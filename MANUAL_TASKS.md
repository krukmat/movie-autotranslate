# Manual Tasks & Backlog

## Immediate Manual Tasks
1. **Download Whisper weights**  
   ```bash
   mkdir -p models/whisper
   python -m faster_whisper.download --model small --output_dir models/whisper
   ```  
   Adjust `ASR_MODEL_DIR` if you stage the checkpoint elsewhere.
2. **Fetch Piper voice models (EN/ES/FR/DE)**  
   Download `.onnx` and matching `.onnx.json` files from https://github.com/rhasspy/piper/releases and place them in `models/piper/`. Example:  
   ```bash
   curl -L -o models/piper/en_US-amy-medium.onnx.gz https://...
   gunzip models/piper/en_US-amy-medium.onnx.gz
   curl -L -o models/piper/en_US-amy-medium.onnx.json https://...
   ```  
   Update `PIPER_VOICES` env var if you choose different voices.
3. **Install CLI prerequisites (run once per workstation/CI runner)**  
   ```bash
   brew install ffmpeg              # or apt/yum equivalent
   pip install piper-tts demucs     # ensures `piper` and `demucs` binaries exist
   ```  
   Adjust PATH or virtualenv activation so the worker container (or host) can invoke these commands.
4. **Rebuild the stack with models mounted**  
   ```bash
   make down
   make up
   ```  
   Ensure `/workspace/models` is populated inside the worker container.
5. **Run the demo smoke test**  
   ```bash
   python scripts/seed_demo.py
   ```  
   Watch the Celery logs (`make logs`) until the job reaches `DONE`.
6. **Execute test suites**  
   ```bash
   (cd backend && pytest)
   (cd workers && pytest)
   (cd web && npm test)
   (cd mobile && npm test)
   ```  
   Confirm lint/type-check commands succeed if configured.
7. **Manual verification**  
   - Hit `http://localhost:8000/metrics` and ensure Prometheus counters render.  
   - Play the HLS output via web/mobile clients; confirm audio sync and track switching.  
   - Inspect MinIO buckets (`raw/proc/pub`) for expected artifacts.
8. **Optional: enable Demucs separation**  
   Install Demucs (`pip install demucs`), set `MIX_USE_DEMUCS=1`, and ensure the CLI generates `no_vocals.wav` under `mix/<lang>/demucs/`. Adjust `DEMUCS_MODEL` if you prefer an alternate preset.

## Backlog & Future Enhancements
- Integrate real diarization using pyannote to replace the stub in `workers/diarization/basic.py`.
- Implement music/FX stem separation (Demucs) and loudness metering aligned with –16 LUFS.
- Extend API coverage: add job list pagination, resume endpoints, and more negative-path tests.
- Provide retry/resume controls in the web dashboard and expose worker logs per stage.
- Package an optional Express gateway (`02b_backend_express.md`) for JS-first deployments.
- Harden security: signed download URLs per request, configurable upload caps, and secrets management templates.
- Expand mobile app to support uploads via multipart/chunked presigned PUT, not just monitoring.
- Automate CI pipelines (GitHub Actions) to run lint/tests and compose-based smoke tests on pull requests.
