.DEFAULT_GOAL := help

.PHONY: help database-up database-down backend-install backend-run backend-test backend-migrate backend-seed frontend-install frontend-run

help:
	@echo "database-up      Start MySQL"
	@echo "database-down    Stop MySQL"
	@echo "backend-install  Install backend dependencies"
	@echo "backend-run      Run the FastAPI API"
	@echo "backend-test     Run backend tests"
	@echo "backend-migrate  Apply database migrations"
	@echo "backend-seed     Create optional demo data (requires SEED_PASSWORD)"
	@echo "frontend-install Install frontend dependencies"
	@echo "frontend-run     Run the Vite application"

database-up:
	docker compose up -d mysql

database-down:
	docker compose down

backend-install:
	python3 -m pip install -r backend/requirements.txt

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && pytest

backend-migrate:
	cd backend && alembic upgrade head

backend-seed:
	cd backend && python -m app.utils.seed_demo --password "$(SEED_PASSWORD)"

frontend-install:
	cd frontend && pnpm install

frontend-run:
	cd frontend && pnpm dev
