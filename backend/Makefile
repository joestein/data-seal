.PHONY: help install test lint format migrate dev worker docker-up docker-down clean security

# Default target
.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (including dev extras)
	pip install -e ".[dev]"

test: ## Run all tests with coverage
	pytest tests/ --cov=dataseal --cov-report=term-missing --cov-report=xml -v

test-fast: ## Run tests without coverage (faster iteration)
	pytest tests/ -v

lint: ## Run ruff linter
	ruff check dataseal/ tests/

format: ## Run ruff formatter
	ruff format dataseal/ tests/

format-check: ## Check formatting without making changes (for CI)
	ruff format --check dataseal/ tests/

security: ## Run security scans (pip-audit + bandit)
	pip-audit --require-hashes --disable-pip || pip-audit
	bandit -r dataseal/ -ll --exclude dataseal/email_templates,dataseal/templates

migrate: ## Run pending Alembic migrations
	alembic upgrade head

migrate-down: ## Rollback last Alembic migration
	alembic downgrade -1

migrate-history: ## Show Alembic migration history
	alembic history --verbose

dev: ## Start development server with hot reload
	uvicorn dataseal.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Start Celery worker (all queues)
	celery -A dataseal.tasks.celery_app worker --loglevel=info --concurrency=4 -Q celery,emails,documents,webhooks,finalize

beat: ## Start Celery beat scheduler
	celery -A dataseal.tasks.celery_app beat --loglevel=info

docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker Compose services
	docker compose down

docker-build: ## Rebuild Docker image
	docker compose build

docker-logs: ## Tail logs from all Docker Compose services
	docker compose logs -f

clean: ## Remove caches, build artifacts, and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage coverage.xml 2>/dev/null || true
