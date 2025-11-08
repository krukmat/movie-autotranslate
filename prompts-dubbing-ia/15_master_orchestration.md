# Master Orchestration Prompt (For the Code-Gen Agent)

## Task
Using all prompts in `/prompts-dubbing-ia`, generate a runnable monorepo with:
- `backend/` (FastAPI), `workers/` (Python), `web/` (React), `mobile/` (React Native), `ops/` (compose).
- Implements the pipeline: ASR → MT → TTS → ALIGN/MIX → PACKAGE → PUBLISH.
- Ships with `make up` and a sample demo job EN→ES.

## Notes
- Prefer Piper for TTS by default; optional XTTS if `GPU=1`.
- Keep code modular; interfaces typed; comprehensive README.
- Use environment variables for model sizes and paths.
