# DataSeal

Self-hosted electronic signature and document management platform. Upload PDFs, place signature fields with a drag-and-drop editor, route documents to recipients for signing, and produce tamper-evident completed documents with full audit trails.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> data-seal && cd data-seal

# 2. Set a secret key (the only required configuration)
#    Generate a strong value:
python -c "import secrets; print(secrets.token_urlsafe(64))"
#    Then open docker-compose.yml and replace the SECRET_KEY placeholder.

# 3. Start all services
docker compose up --build

# 4. Open the application
open http://localhost:3000

# 5. (Optional) Browse interactive API docs
open http://localhost:18000/docs
```

Emails sent during development are captured by MailHog at http://localhost:8025.

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker | 24+ |
| Docker Compose | v2 |
| Python (local backend dev) | 3.11+ |
| Node.js (local frontend dev) | 20+ |

## Installation

### Docker (recommended)

Docker Compose starts seven services: `frontend` (React SPA on port 3000), `app` (FastAPI on port 18000), `celery-worker`, `celery-beat`, `db` (PostgreSQL 16 on port 15432), `valkey` (Valkey 8 on port 6379), and `mailhog` (SMTP capture on port 8025).

Database migrations run automatically on `app` startup via `alembic upgrade head`.

```bash
docker compose up --build
```

### Local Development — Backend

```bash
cd backend

# Install dependencies including dev extras
pip install -e ".[dev]"

# Start only the infrastructure services
docker compose up db valkey mailhog -d

# Copy and configure environment
cp .env.example .env
# Edit DATABASE_URL / DATABASE_URL_SYNC to use localhost:5432 instead of db:5432

# Run migrations
python -m alembic upgrade head

# Start the API server
uvicorn dataseal.main:app --reload --port 8000

# In a separate terminal, start a Celery worker
celery -A dataseal.tasks.celery_app worker --loglevel=info -Q celery,emails,documents,webhooks,finalize
```

### Local Development — Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 5173, proxies /api requests to localhost:18000)
npm run dev
```

The Vite dev server proxies all `/api` requests to the backend, so the frontend works against a locally running API without any CORS configuration.

## Usage

### Web Interface

Navigate to http://localhost:3000 and register an account. The interface provides:

- **Dashboard** — search and filter envelopes by status
- **Envelope creator** — 4-step wizard: upload documents, add recipients, place fields with drag-and-drop editor, review and send
- **Envelope detail** — view status, recipients, audit trail, download completed documents
- **Signing experience** — recipients open their unique link and sign with draw, type, or upload
- **Templates** — reusable envelope structures
- **PowerForms** — self-service signing links with a public URL
- **Webhooks** — configure event delivery to external systems
- **Settings** — profile, API keys, OAuth application management

### REST API

```bash
BASE=http://localhost:18000/api/v1

# Register
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"s3curePass!","full_name":"Jane Smith"}'

# Login — returns access_token and refresh_token
curl -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"s3curePass!"}'

TOKEN="<access_token from login>"

# Create envelope, upload PDF, add recipient, place field, send
curl -X POST $BASE/envelopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Service Agreement","message":"Please review and sign."}'
```

See [API Reference](#api-reference) below or the interactive docs at `/docs` for the full endpoint list.

## Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        BROWSER[Web Browser<br/>React SPA — port 3000]
        APICLIENT[API Client / SDK]
    end

    subgraph "Application Layer"
        FASTAPI[FastAPI<br/>port 18000 external<br/>port 8000 internal]
        WORKER[Celery Worker<br/>PDF rendering, email,<br/>webhooks, finalization]
        BEAT[Celery Beat<br/>Scheduled retries]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 16<br/>port 15432 external)]
        VALKEY[(Valkey 8<br/>port 6379)]
        FS[File Storage<br/>Local / S3-compatible]
    end

    subgraph "Dev Tools"
        MAILHOG[MailHog<br/>SMTP capture — port 8025]
    end

    BROWSER -->|HTTP REST| FASTAPI
    APICLIENT -->|HTTP REST| FASTAPI
    FASTAPI -->|Read/Write| PG
    FASTAPI -->|JWT blocklist / sessions| VALKEY
    FASTAPI -->|Upload/Download| FS
    FASTAPI -->|Enqueue tasks| VALKEY
    WORKER -->|Consume tasks| VALKEY
    WORKER -->|Read/Write| PG
    WORKER -->|Read files| FS
    WORKER -->|Send email| MAILHOG
    WORKER -->|POST events| WEBHOOKS[Webhook Endpoints]
    BEAT -->|Schedule retries| VALKEY
```

### Component Overview

| Component | Role |
|-----------|------|
| **React SPA** | Full UI for envelope management, field placement, signing, templates, webhooks |
| **FastAPI** | REST API, authentication, request validation, ownership checks |
| **Celery Worker** | PDF rendering, email sending, document finalization, webhook delivery |
| **Celery Beat** | Scheduled retry of failed webhook deliveries |
| **PostgreSQL** | All persistent data (envelopes, documents, recipients, fields, audit trail) |
| **Valkey** | Celery task broker, JWT revocation blocklist |
| **File storage** | Original PDFs, rendered page images, completed signed documents |
| **MailHog** | Local SMTP capture for development |

### Envelope Lifecycle

```
created --> sent --> delivered --> signed --> completed
     \          \                       \--> declined (any recipient declines)
      \          \--> voided
       \--> voided
```

## API Reference

Base URL: `http://localhost:18000/api/v1`

Interactive documentation: `/docs` (Swagger UI) and `/redoc`.

| Resource | Endpoints |
|----------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` |
| API Keys | `GET/POST /auth/api-keys`, `DELETE /auth/api-keys/{id}` |
| Envelopes | `GET/POST /envelopes`, `GET/PATCH/DELETE /envelopes/{id}`, `/send`, `/void`, `/resend`, `/audit-trail`, `/certificate`, `/combined` |
| Documents | `GET/POST /envelopes/{id}/documents`, `GET/DELETE /envelopes/{id}/documents/{doc_id}`, `/download`, `/pages` |
| Recipients | `GET/POST /envelopes/{id}/recipients`, `GET/PATCH/DELETE /envelopes/{id}/recipients/{rid}` |
| Fields | `GET/POST /envelopes/{id}/documents/{doc_id}/fields`, `GET/PATCH/DELETE .../fields/{fid}` |
| Signing (public) | `GET /signing/{token}`, `PUT /signing/{token}/fields/{fid}`, `POST /signing/{token}/complete`, `POST /signing/{token}/decline` |
| Templates | `GET/POST /templates`, `GET/PATCH/DELETE /templates/{id}`, sub-resources, `POST /templates/{id}/create-envelope` |
| PowerForms | `GET/POST /powerforms`, `GET/PATCH/DELETE /powerforms/{id}`, `GET /p/{slug}` (public) |
| Webhooks | `GET/POST /webhooks`, `GET/PATCH/DELETE /webhooks/{id}`, `/deliveries`, `/test` |
| OAuth 2.0 | `GET/POST /oauth/apps`, `GET /oauth/authorize`, `POST /oauth/token`, `POST /oauth/revoke` |

## Configuration

All configuration is via environment variables. Set them in `backend/.env` for local development or as container environment variables in production. The only required variable is `SECRET_KEY`.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT signing key — min 32 chars, no weak defaults | — | **Yes** |
| `APP_URL` | Public base URL | `http://localhost:8000` | No |
| `DEBUG` | Enable debug mode (broadens CORS) | `false` | No |
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) | `postgresql+asyncpg://dataseal:dataseal@localhost:5432/dataseal` | No |
| `DATABASE_URL_SYNC` | Sync PostgreSQL URL for Celery/Alembic | `postgresql://dataseal:dataseal@localhost:5432/dataseal` | No |
| `VALKEY_URL` | Valkey connection URL | `redis://localhost:6379/0` | No |
| `SMTP_HOST` | SMTP server hostname | `localhost` | No |
| `SMTP_PORT` | SMTP server port | `1025` | No |
| `SMTP_USER` | SMTP username | `` | No |
| `SMTP_PASSWORD` | SMTP password | `` | No |
| `SMTP_FROM_ADDRESS` | Sender address for outgoing email | `noreply@dataseal.example.com` | No |
| `SMTP_FROM_NAME` | Sender display name | `DataSeal` | No |
| `SMTP_USE_TLS` | Enable SMTP TLS | `false` | No |
| `STORAGE_BACKEND` | Storage driver (`local`) | `local` | No |
| `STORAGE_LOCAL_PATH` | Root directory for local file storage | `/data/storage` | No |
| `SIGNING_TOKEN_EXPIRY_HOURS` | Hours until signing links expire | `72` | No |
| `MAX_DOCUMENT_SIZE_MB` | Max PDF upload size in MB | `25` | No |
| `MAX_DOCUMENTS_PER_ENVELOPE` | Max PDFs per envelope | `10` | No |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per client per minute | `100` | No |
| `ACCESS_TOKEN_EXPIRY_MINUTES` | JWT access token lifetime | `15` | No |
| `REFRESH_TOKEN_EXPIRY_DAYS` | JWT refresh token lifetime | `7` | No |

## Development

### Backend

```bash
cd backend

# Run all tests (SQLite in-memory, no Docker required)
pytest

# Run with coverage
pytest --cov=dataseal --cov-report=term-missing

# Lint
ruff check dataseal/ tests/

# Format
ruff format dataseal/ tests/

# Type check
mypy dataseal/

# Create a new migration after changing models
python -m alembic revision --autogenerate -m "describe the change"

# Apply migrations
python -m alembic upgrade head
```

The test suite covers unit, API, and integration layers. Celery tasks are mocked; no running worker is needed.

### Frontend

```bash
cd frontend

# Run tests (Vitest, jsdom)
npm test

# Run with coverage
npm run test:coverage

# Lint (ESLint)
npm run lint

# Type check
npm run typecheck

# Production build
npm run build
```

### CI

GitHub Actions runs on every push and pull request:

- **backend-lint** — ruff + mypy
- **backend-test** — pytest with coverage
- **frontend-lint** — ESLint + TypeScript type check
- **frontend-build** — Vite production build verification

## Security

- JWT access tokens have a 15-minute lifetime. Logout revokes the token JTI via a Valkey blocklist.
- Passwords are bcrypt-hashed (12 rounds). API keys are bcrypt-hashed with an 8-character prefix stored in plaintext for fast lookup.
- Webhook URLs are validated at registration to block SSRF against internal/private IP ranges and cloud metadata endpoints.
- Webhook payloads are signed with HMAC-SHA256 using a per-endpoint secret stored encrypted at rest.
- Completed documents include a SHA-256 tamper-evidence hash appended to the certificate of completion.
- `SECRET_KEY` is required at startup; the application refuses to start if it is absent, empty, shorter than 32 characters, or matches a known weak value.
- JWT access tokens are stored in Zustand memory in the frontend and are never persisted to localStorage or cookies.

To report a security vulnerability, open a private GitHub Security Advisory or contact the maintainers directly.

## License

See [LICENSE](LICENSE).
