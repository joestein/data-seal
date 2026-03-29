# DataSeal — CLAUDE.md

Instructions for AI assistants working on this codebase.

## Project Purpose

DataSeal is a self-hosted electronic signature platform (DocuSign clone). It allows users to upload PDFs, place signature fields, route documents to recipients for signing, and produce tamper-evident completed documents with full audit trails.

## Key Commands

```bash
# Start everything (recommended for development)
docker compose up

# Run tests (no Docker needed — SQLite in-memory)
pytest

# Run a single test file
pytest tests/test_api_envelopes.py -v

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy dataseal/

# Apply database migrations
python -m alembic upgrade head

# Generate a new migration after model changes
python -m alembic revision --autogenerate -m "describe the change"

# Start the dev API server (requires db + valkey running)
uvicorn dataseal.main:app --reload --port 8000

# Start a Celery worker (requires valkey running)
celery -A dataseal.tasks.celery_app worker --loglevel=info -Q celery,emails,documents,webhooks,finalize
```

## Architecture Summary

- **FastAPI** (`dataseal/main.py`) — app factory, mounts 10 routers under `/api/v1`
- **PostgreSQL** — primary persistence via async SQLAlchemy ORM
- **Valkey** — Celery task broker + JWT revocation blocklist
- **Celery Worker** — PDF rendering, email sending, document finalization, webhook delivery
- **File storage** — `dataseal/storage.py` provides a `StorageBackend` ABC; `LocalStorageBackend` stores files under `STORAGE_LOCAL_PATH`

All routers live in `dataseal/api/`. Auth dependencies live in `dataseal/api/deps.py`.

## File Structure

```
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
    base.py            # Base, UUIDMixin (uuid7), TimestampMixin
    user.py            # User, ApiKey
    envelope.py        # Envelope (includes can_transition_to() state machine)
    document.py        # Document
    recipient.py       # Recipient (signing token, status)
    field.py           # DocumentField (percentage coordinates)
    audit.py           # AuditEvent (append-only)
    template.py        # Template, TemplateDocument, TemplateRecipient, TemplateField
    webhook.py         # WebhookEndpoint, WebhookDelivery
    powerform.py       # PowerForm
    oauth.py           # OAuthApp
  schemas/             # Pydantic request/response schemas (mirrors models/)
  services/
    audit.py           # create_audit_event() helper
    envelope.py        # send_envelope(), validate_for_sending(), check_completion()
    signing.py         # get_recipient_by_token(), validate_token(), complete_signing()
  tasks/
    celery_app.py      # Celery config, queues, beat schedule
    emails.py          # send_signing_emails, send_completed_emails, etc.
    documents.py       # render_document_pages (PDF -> PNG via pdf2image)
    finalize.py        # finalize_envelope (signature overlay + certificate PDF)
    webhooks.py        # deliver_webhook (HMAC-SHA256, exponential backoff)
  security/
    token_blocklist.py # Valkey-based JWT JTI blocklist
    encryption.py      # encrypt_value / decrypt_value for webhook secrets
    url_validation.py  # SSRF prevention for webhook URLs
    oauth_codes.py     # Valkey-backed OAuth authorization code store
  email_templates/     # Jinja2 HTML email templates
  templates/           # Server-rendered Jinja2 pages (signing.html, powerform.html)
alembic/
  versions/            # Migration scripts (001_initial_schema.py)
tests/
  conftest.py          # SQLite fixtures, auth helpers, Celery mocks
  test_unit_*.py       # Pure logic tests (no DB, no HTTP)
  test_api_*.py        # FastAPI TestClient tests
  test_integration_*.py # Multi-step workflow tests
```

## Code Conventions

### Models
- All primary keys are `uuid7` (import from `uuid_extensions`).
- `TimestampMixin` adds `created_at` / `updated_at` automatically.
- The `Envelope` model has a `can_transition_to(status)` method that enforces the state machine — always call this before changing envelope status.
- Audit events must be recorded for every meaningful state change using `create_audit_event()` from `dataseal/services/audit.py`.

### API Layer
- All API endpoints follow the `get_current_user` dependency pattern from `dataseal/api/deps.py`.
- Envelope ownership is enforced by `get_envelope_dep` — use it as a dependency on all envelope-scoped routes.
- Write-mutating endpoints should use `require_scope("write", "resource:action")` as a dependency.
- Only envelopes in `created` status can have their documents, recipients, or fields modified.

### Celery Tasks
- Tasks use synchronous SQLAlchemy sessions (not async) since Celery does not natively support async.
- Import `get_sync_session` from `dataseal/database.py` inside task bodies.
- Do not call `.delay()` in tests without mocking; the conftest patches tasks automatically.

### Schemas
- Input schemas (Create/Update) live in `dataseal/schemas/`.
- Response schemas always use `model_config = ConfigDict(from_attributes=True)` so they can be constructed from ORM instances.

### Field Coordinates
- `x_position`, `y_position`, `width`, `height` are all floats in the range `0.0`–`100.0`, representing percentages of the page dimensions.
- `page_number` is 1-based.

### Storage Paths
- Files are stored at `{STORAGE_LOCAL_PATH}/documents/{envelope_id}/{doc_id}/original.pdf`
- Page images: `documents/{envelope_id}/{doc_id}/pages/page_{n}.png`
- Completed output: `documents/{envelope_id}/completed/final.pdf` and `certificate.pdf`

## Authentication

Two authentication methods are supported:

1. **JWT Bearer token** — obtained via `POST /api/v1/auth/login`. Use `Authorization: Bearer <token>` header. Access tokens expire after 15 minutes; use `POST /api/v1/auth/refresh` with a refresh token to get a new pair.

2. **API Key** — created via `POST /api/v1/auth/api-keys`. Keys are prefixed with `ds_key_` and shown once at creation. Pass as `Authorization: Bearer <api_key>`. Scopes are enforced.

## Common Tasks

### Adding a new API endpoint
1. Add the route to the appropriate file in `dataseal/api/`.
2. Add Pydantic schemas to `dataseal/schemas/` if needed.
3. Add a test to the corresponding `tests/test_api_*.py` file.
4. If the endpoint changes ownership rules, update `get_envelope_dep` or add an equivalent ownership check.

### Adding a database model
1. Create the model in `dataseal/models/`, inheriting from `Base` with `UUIDMixin` and `TimestampMixin`.
2. Export it from `dataseal/models/__init__.py`.
3. Run `python -m alembic revision --autogenerate -m "add <model>"`.
4. Review and apply the migration.

### Adding a Celery task
1. Add the task to the appropriate file in `dataseal/tasks/` (or create a new file).
2. Register the task queue in `dataseal/tasks/celery_app.py` if it needs a dedicated queue.
3. Mock the task in tests using `unittest.mock.patch` (see `tests/conftest.py` for patterns).

## Environment Variables

See `.env.example` for the full list. The only required variable is `SECRET_KEY`. All others have defaults suitable for local development.

`SECRET_KEY` is validated at startup: it must be at least 32 characters long and must not match any known weak value. Generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Known Limitations

- OAuth authorization codes are stored in Valkey (`dataseal/security/oauth_codes.py`) with a 10-minute TTL and atomic consume.
- Rate limiting is configured in settings (`RATE_LIMIT_PER_MINUTE`) but the `slowapi` middleware is not yet mounted. All endpoints are currently unthrottled.
- The signing page uses typed-name signatures rendered as base64 text, not canvas-drawn signatures.
- Celery tasks use synchronous SQLAlchemy sessions; async operations inside tasks require `asyncio.run()` wrappers.
