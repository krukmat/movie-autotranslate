# Prompts Pack — AI Dubbing MVP (Free/OSS Stack)

This folder contains **layered prompts** to feed Codex/Claude Code (or similar) so they can generate a working MVP where a user uploads a movie in language **X** and receives the **same movie dubbed by AI** in language **Y** (EN/ES/FR/DE).

**Start with:** `15_master_orchestration.md`  
Then pass each specialized prompt to focused agents (Architect, Backend, ML, Audio, Web, Mobile, DevOps, QA).

Stack defaults:
- FastAPI + Python workers
- Redis + Celery
- MinIO (S3)
- LibreTranslate
- Piper TTS (default); Coqui XTTS-v2 optional (GPU)
- FFmpeg HLS with alternate audio + VTT
- React (web) + React Native (mobile)

All prompts are in English for best compatibility with code-gen tools.
