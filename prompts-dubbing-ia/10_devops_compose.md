# DevOps Prompt — Docker Compose & Makefile

## Objective
Provide a `docker-compose.yml` that boots the full stack locally and a `Makefile` for common tasks.

## Services
- `api` (FastAPI on :8000)
- `worker` (Python worker)
- `redis`
- `minio` (+ mc for bucket init)
- `libretranslate`
- `nginx-hls` (serving `/pub` from a volume)

## Tasks
- Makefile: `make up`, `make down`, `make logs`, `make seed`, `make demo`.
- Seed: upload sample video, run a demo EN→ES job, open web player.

## Acceptance
- `make up` brings up all; health endpoints pass; demo job finishes with HLS master.
