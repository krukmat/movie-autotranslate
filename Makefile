COMPOSE = docker compose -f ops/docker-compose.yml

.PHONY: up down logs demo seed

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f --tail=100

seed:
	python scripts/seed_demo.py

demo:
	$(COMPOSE) up -d --build
	python scripts/seed_demo.py
