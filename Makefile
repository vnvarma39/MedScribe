.PHONY: up down build seed logs test clean dev-backend dev-dashboard

## ── Docker Commands ─────────────────────────────────────────────────────────
up:          ## Start all services with Docker Compose
	docker-compose up --build -d
	@echo "\n✅  MedScribe is running!"
	@echo "   📡  API:       http://localhost:8000"
	@echo "   📚  Docs:      http://localhost:8000/docs"
	@echo "   📊  Dashboard: http://localhost:8501\n"

down:        ## Stop all services
	docker-compose down

build:       ## Build Docker images without starting
	docker-compose build

logs:        ## Tail logs for all services
	docker-compose logs -f

logs-backend:  ## Tail backend logs only
	docker-compose logs -f backend

logs-dashboard:  ## Tail dashboard logs only
	docker-compose logs -f dashboard

## ── Local Development ───────────────────────────────────────────────────────
dev-backend:  ## Run FastAPI backend locally (requires venv)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-dashboard:  ## Run Streamlit dashboard locally
	cd dashboard && streamlit run app.py --server.port 8501

## ── Database ─────────────────────────────────────────────────────────────────
seed:        ## Seed the database with sample clinical notes (server must be running)
	python data/seed.py

## ── Testing ──────────────────────────────────────────────────────────────────
test:        ## Run pytest suite
	cd backend && pytest tests/ -v --tb=short

test-cov:    ## Run tests with coverage report
	cd backend && pytest tests/ -v --cov=app --cov-report=html

## ── Cleanup ──────────────────────────────────────────────────────────────────
clean:       ## Remove containers, volumes, and local DB
	docker-compose down -v
	rm -f data/medscribe.db data/medscribe.db-shm data/medscribe.db-wal
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
