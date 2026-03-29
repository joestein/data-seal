# DataSeal

Self-hosted electronic signature and agreement management platform — a DocuSign-compatible REST API built with Python, FastAPI, PostgreSQL, and Celery.

## Quick Start

```bash
# 1. Clone and enter the directory
git clone <repo-url> data-seal && cd data-seal

# 2. Copy and configure environment variables
cp .env.example .env
# Generate a strong secret key:
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Paste the output as SECRET_KEY in .env

# 3. Start all services
docker compose up

# 4. The API is now live
curl http://localhost:8000/health
# -> {"status":"ok","db":"ok","valkey":"ok"}

# 5. Browse interactive API docs
open http://localhost:8000/docs
```

> Emails are captured locally by MailHog at http://localhost:8025

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker | 24+ |
| Docker Compose | v2 |
| Python (local dev only) | 3.11+ |

## Installation

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY to a strong random value
docker compose up --build
```

Docker Compose starts six services: `app` (FastAPI on port 8000), `celery-worker`, `celery-beat`, `db` (PostgreSQL 16), `valkey` (Valkey 8), and `mailhog`.

Database migrations run automatically on `app` startup via `alembic upgrade head`.

### Local Development

```bash
# Install uv (package manager)
pip install uv

# Create virtualenv and install all dependencies including dev extras
uv sync --extra dev

# Start infrastructure only
docker compose up db valkey mailhog -d

# Copy and edit .env
cp .env.example .env
# Set DATABASE_URL and DATABASE_URL_SYNC to point at localhost:5432

# Run migrations
python -m alembic upgrade head

# Start the API server
uvicorn dataseal.main:app --reload --port 8000

# In a separate terminal, start a Celery worker
celery -A dataseal.tasks.celery_app worker --loglevel=info -Q celery,emails,documents,webhooks,finalize
```

## Usage

### Register and authenticate

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"s3curePass!","full_name":"Jane Smith"}'

# Login — returns access_token and refresh_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"s3curePass!"}'
```

### Create and send an envelope

```bash
TOKEN="<access_token from login>"

# 1. Create an envelope
curl -X POST http://localhost:8000/api/v1/envelopes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Service Agreement","message":"Please review and sign."}'

ENVELOPE_ID="<id from response>"

# 2. Upload a PDF document
curl -X POST http://localhost:8000/api/v1/envelopes/$ENVELOPE_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@contract.pdf"

DOC_ID="<id from response>"

# 3. Add a recipient
curl -X POST http://localhost:8000/api/v1/envelopes/$ENVELOPE_ID/recipients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob Jones","email":"bob@example.com","role":"signer","routing_order":1}'

RECIPIENT_ID="<id from response>"

# 4. Place a signature field (percentage-based coordinates, 1-based page numbers)
curl -X POST "http://localhost:8000/api/v1/envelopes/$ENVELOPE_ID/documents/$DOC_ID/fields" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id":"'"$RECIPIENT_ID"'",
    "type":"signature",
    "page_number":1,
    "x_position":60,"y_position":85,
    "width":25,"height":5,
    "is_required":true
  }'

# 5. Send — triggers signing emails via Celery
curl -X POST http://localhost:8000/api/v1/envelopes/$ENVELOPE_ID/send \
  -H "Authorization: Bearer $TOKEN"
```

The recipient receives an email with a unique signing link. When they complete signing, Celery generates the final PDF with embedded signatures and appends a certificate of completion.

## Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        APICLIENT[API Client / SDK]
    end

    subgraph "Application Layer"
        FASTAPI[FastAPI Application<br/>Port 8000]
        WORKER[Celery Worker<br/>Async Tasks]
        BEAT[Celery Beat<br/>Scheduled Tasks]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 16<br/>Primary Database)]
        VALKEY[(Valkey 8<br/>Cache + Task Broker)]
        FS[File Storage<br/>Local / S3-compatible]
    end

    subgraph "External Services"
        SMTP[SMTP<br/>Email Delivery]
        WHOOK[Webhook Endpoints<br/>Customer Servers]
    end

    WEB -->|HTTP| FASTAPI
    APICLIENT -->|REST| FASTAPI
    FASTAPI -->|Read/Write| PG
    FASTAPI -->|Token blocklist / sessions| VALKEY
    FASTAPI -->|Upload/Download| FS
    FASTAPI -->|Enqueue tasks| VALKEY
    WORKER -->|Consume tasks| VALKEY
    WORKER -->|Read/Write| PG
    WORKER -->|Read files| FS
    WORKER -->|Send email| SMTP
    WORKER -->|POST events| WHOOK
    BEAT -->|Scheduled jobs| VALKEY
```

### Component overview

| Component | Role |
|-----------|------|
| **FastAPI** | REST API, authentication, request validation, ownership checks |
| **Celery Worker** | PDF rendering, email sending, document finalization, webhook delivery |
| **Celery Beat** | Scheduled retry of pending webhook deliveries |
| **PostgreSQL** | All persistent data (envelopes, documents, recipients, audit trail) |
| **Valkey** | Celery task broker, JWT revocation blocklist |
| **File storage** | Original PDFs, rendered page images, completed documents |
| **MailHog** | Local SMTP capture for development |

### Envelope lifecycle

```
created --> sent --> delivered --> signed --> completed
     \          \                       \--> (if any recipient declines) declined
      \          \--> voided
       \--> voided
```

## API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive documentation is available at `/docs` (Swagger UI) and `/redoc`.

| Resource | Endpoints |
|----------|-----------|
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me` |
| API Keys | `/auth/api-keys` |
| Envelopes | `/envelopes`, `/envelopes/{id}`, `/envelopes/{id}/send`, `/void`, `/resend`, `/audit-trail`, `/certificate`, `/combined` |
| Documents | `/envelopes/{id}/documents`, `/envelopes/{id}/documents/{doc_id}`, `/download`, `/pages` |
| Recipients | `/envelopes/{id}/recipients`, `/envelopes/{id}/recipients/{rid}` |
| Fields | `/envelopes/{id}/documents/{doc_id}/fields` |
| Signing (public) | `/signing/{token}`, `/signing/{token}/fields/{fid}`, `/signing/{token}/complete`, `/signing/{token}/decline` |
| Templates | `/templates`, `/templates/{id}`, plus document/recipient/field sub-resources, `/templates/{id}/create-envelope` |
| PowerForms | `/powerforms`, `/powerforms/{id}`, `/p/{slug}` (public) |
| Webhooks | `/webhooks`, `/webhooks/{id}`, `/webhooks/{id}/deliveries`, `/webhooks/{id}/test` |
| OAuth 2.0 | `/oauth/apps`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke` |

See [docs/API.md](docs/API.md) for the full reference with request/response schemas.

## Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT signing key (min 32 chars, no weak defaults) | — | **Yes** |
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
| `STORAGE_LOCAL_PATH` | Root directory for file storage | `/data/storage` | No |
| `SIGNING_TOKEN_EXPIRY_HOURS` | Hours until signing links expire | `72` | No |
| `MAX_DOCUMENT_SIZE_MB` | Max PDF upload size | `25` | No |
| `MAX_DOCUMENTS_PER_ENVELOPE` | Max PDFs per envelope | `10` | No |
| `ACCESS_TOKEN_EXPIRY_MINUTES` | JWT access token lifetime | `15` | No |
| `REFRESH_TOKEN_EXPIRY_DAYS` | JWT refresh token lifetime | `7` | No |

## Development

```bash
# Run all tests (no Docker needed — uses SQLite in-memory)
pytest

# Run with coverage report
pytest --cov=dataseal --cov-report=term-missing

# Lint
ruff check .

# Type check
mypy dataseal/

# Format
ruff format .

# Create a new migration after changing models
python -m alembic revision --autogenerate -m "describe the change"

# Apply migrations
python -m alembic upgrade head
```

The test suite contains 230 tests across unit, API, and integration layers. Celery tasks are mocked; no running worker is needed.

## Security

- JWT access tokens (15 min lifetime). Logout revokes the token JTI via a Valkey blocklist.
- Passwords are bcrypt-hashed (12 rounds). API keys are bcrypt-hashed with an 8-character prefix stored for fast lookup.
- Webhook URLs are validated at registration to block SSRF against internal/private IP ranges and cloud metadata endpoints.
- Webhook payloads are signed with HMAC-SHA256 using a per-endpoint secret stored encrypted at rest.
- Completed documents include a SHA-256 tamper-evidence hash appended to the certificate of completion.
- `SECRET_KEY` is required at startup; the application refuses to start if it is absent, empty, shorter than 32 characters, or matches a known weak value.

To report a security vulnerability, open a private GitHub Security Advisory or contact the maintainers directly.

## License

See [LICENSE](LICENSE).
