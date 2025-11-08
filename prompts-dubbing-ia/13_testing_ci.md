# Testing & CI Prompt

## Objective
Ship a credible MVP with automated tests and a demo clip.

## Tests
- Backend: unit tests for routes, job orchestration, error paths.
- ML: golden tests on a short audio (ASR outputs ~expected tokens; TTS roundtrip within duration tolerance).
- Audio: check loudness and silence padding invariants.
- E2E: upload → job → HLS playback (headless via stream probe).

## CI
- GitHub Actions: lint, type-check, tests, build images, compose up smoke test.
