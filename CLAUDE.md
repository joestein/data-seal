# DataSeal — CLAUDE.md

Instructions for AI assistants working on this codebase.

## Project Purpose

DataSeal is a self-hosted electronic signature platform (DocuSign clone). It allows users to upload PDFs, place signature fields, route documents to recipients for signing, and produce tamper-evident completed documents with full audit trails.

## Monorepo Structure

```
data-seal/
  backend/          # FastAPI + Celery + PostgreSQL + Valkey
  frontend/         # React 18 + TypeScript + Vite 6 + Tailwind CSS
  docker-compose.yml
  .github/workflows/ci.yml
```

## Key Commands

### Docker (recommended — runs everything)

```bash
# Start all services (API, frontend, Celery, DB, Valkey, MailHog)
docker compose up --build

# Ports exposed:
#   http://localhost:3000      frontend (nginx)
#   http://localhost:18000     backend API
#   http://localhost:18000/docs  Swagger UI
#   http://localhost:8025      MailHog (captured emails)
#   localhost:15432            PostgreSQL
#   localhost:6379             Valkey
```

### Backend (run from `backend/`)

```bash
# Install dependencies (includes dev extras for pytest, mypy, ruff)
cd backend && pip install -e ".[dev]"

# Run tests (no Docker needed — SQLite in-memory)
cd backend && pytest

# Run a single test file
cd backend && pytest tests/test_api_envelopes.py -v

# Run tests with coverage
cd backend && pytest --cov=dataseal --cov-report=term-missing

# Lint
cd backend && ruff check dataseal/ tests/

# Format
cd backend && ruff format dataseal/ tests/

# Type check
cd backend && mypy dataseal/

# Apply database migrations
cd backend && python -m alembic upgrade head

# Generate a new migration after model changes
cd backend && python -m alembic revision --autogenerate -m "describe the change"

# Start the dev API server (requires db + valkey running)
cd backend && uvicorn dataseal.main:app --reload --port 8000

# Start a Celery worker (requires valkey running)
cd backend && celery -A dataseal.tasks.celery_app worker --loglevel=info -Q celery,emails,documents,webhooks,finalize
```

### Frontend (run from `frontend/`)

```bash
# Install dependencies
cd frontend && npm install

# Start dev server with hot reload (port 5173, proxies /api to localhost:18000)
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Run tests (Vitest)
cd frontend && npm test

# Run tests with coverage
cd frontend && npm run test:coverage

# Lint
cd frontend && npm run lint

# Type check
cd frontend && npm run typecheck
```

## Architecture Summary

### Backend
- **FastAPI** (`backend/dataseal/main.py`) — app factory, mounts 10 routers under `/api/v1`
- **PostgreSQL** — primary persistence via async SQLAlchemy ORM
- **Valkey** — Celery task broker + JWT revocation blocklist
- **Celery Worker** — PDF rendering, email sending, document finalization, webhook delivery
- **File storage** — `dataseal/storage.py` provides a `StorageBackend` ABC; `LocalStorageBackend` stores files under `STORAGE_LOCAL_PATH`

### Frontend
- **React 18** with TypeScript — single-page application
- **Vite 6** — dev server with API proxy, production build
- **React Router v6** — client-side routing with nested layouts
- **TanStack Query v5** — server state management with cache invalidation
- **Zustand** — client state (auth tokens, UI state)
- **Tailwind CSS 3** — utility-first styling
- **react-konva** — HTML5 Canvas for drag-and-drop field placement
- **Axios** — HTTP client with JWT interceptors

All routers live in `backend/dataseal/api/`. Auth dependencies live in `backend/dataseal/api/deps.py`.

## File Structure

```
backend/
  dataseal/
    main.py              # FastAPI app factory
    config.py            # Pydantic Settings (all env vars)
    database.py          # Async SQLAlchemy engine + session factory
    storage.py           # StorageBackend ABC + LocalStorageBackend
    api/
      deps.py            # get_current_user, get_envelope_dep, require_scope
      auth.py            # register, login, refresh, logout, profile, API keys
      envelopes.py       # CRUD, send, void, resend, audit trail, downloads
      documents.py       # Upload, list, download, page images
      recipients.py      # Add, list, update, delete
      fields.py          # Add, list, update, delete
      signing.py         # Token-authenticated: session, field values, complete, decline
      templates.py       # CRUD + create-envelope
      powerforms.py      # CRUD + public /p/{slug} endpoints
      webhooks.py        # CRUD + deliveries + test
      oauth.py           # App registration, authorize, token exchange, revoke
    models/
    schemas/
    services/
    tasks/
    security/
    email_templates/
    templates/
  alembic/
  tests/

frontend/
  src/
    api/           # Axios client, typed API modules (one per resource)
    hooks/         # TanStack Query hooks
    stores/        # Zustand stores (auth, UI toasts)
    pages/         # Route pages
    components/    # Reusable UI components
      layout/      # AppShell, Sidebar, Header, ProtectedRoute
      common/      # Button, Input, Modal, Toast, Badge, Pagination, etc.
      envelope/    # EnvelopeCard, AuditTrailViewer, RecipientList, etc.
      wizard/      # 4-step envelope creation wizard
      pdf/         # PdfViewer, PdfPageCanvas, FieldOverlay
      fields/      # FieldPalette, FieldConfigPanel, DraggableField
      signing/     # SignatureModal, SignatureCanvas, signing field types
    lib/           # Constants, utils, route paths
    styles/        # Tailwind globals
```

## Code Conventions

### Models
- All primary keys are `uuid7` (import from `uuid_extensions`).
- `TimestampMixin` adds `created_at` / `updated_at` automatically.
- The `Envelope` model has a `can_transition_to(status)` method that enforces the state machine.
- Audit events must be recorded for every meaningful state change.

### API Layer
- All API endpoints follow the `get_current_user` dependency pattern from `dataseal/api/deps.py`.
- Envelope ownership is enforced by `get_envelope_dep`.
- Write-mutating endpoints should use `require_scope("write", "resource:action")`.
- Only envelopes in `created` status can have their documents, recipients, or fields modified.

### Field Coordinates
- `x_position`, `y_position`, `width`, `height` are all floats in the range `0.0`-`100.0`, representing percentages of the page dimensions.
- `page_number` is 1-based.

### Frontend
- API types in `src/api/types.ts` mirror backend Pydantic schemas.
- JWT access tokens stored in Zustand memory only (never localStorage).
- All API calls go through the Axios instance in `src/api/client.ts` with automatic 401 refresh.
- Field coordinates use percentage system (0-100) matching backend.
- The signing page uses a standalone layout (no sidebar/header) and authenticates via URL token.

## Authentication

Two authentication methods are supported:

1. **JWT Bearer token** — obtained via `POST /api/v1/auth/login`. Access tokens expire after 15 minutes; use `POST /api/v1/auth/refresh` with a refresh token to get a new pair.

2. **API Key** — created via `POST /api/v1/auth/api-keys`. Keys are prefixed with `ds_key_` and shown once at creation.

## Environment Variables

See `backend/.env.example` for the full list. The only required variable is `SECRET_KEY` (must be at least 32 characters). All other variables have working defaults for local development.
