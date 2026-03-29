# DataSeal Deployment Guide

This guide covers production deployment of DataSeal using Docker Compose. For local development, see the [README](../README.md).

---

## Prerequisites

- Docker 24+ and Docker Compose v2
- A server with at least 2 GB RAM and 20 GB disk
- A domain name with TLS termination (e.g., via nginx or a cloud load balancer)
- An SMTP provider for outgoing email

---

## Quick Production Deployment

```bash
# 1. Clone the repository
git clone <repo-url> /opt/dataseal
cd /opt/dataseal

# 2. Create the .env file
cp .env.example .env

# 3. Set required variables (see Configuration section below)
nano .env

# 4. Build and start all services
docker compose up -d --build

# 5. Verify health
curl http://localhost:8000/health
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure these values before starting.

### Required

| Variable | Description | How to generate |
|----------|-------------|-----------------|
| `SECRET_KEY` | JWT signing key. Must be at least 32 characters and not a known weak value. | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |

### Application

| Variable | Default | Notes |
|----------|---------|-------|
| `APP_URL` | `http://localhost:8000` | Set to your public domain, e.g. `https://sign.yourcompany.com` |
| `DEBUG` | `false` | Never set to `true` in production. Enabling debug broadens CORS to all origins. |

### Database

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://dataseal:dataseal@db:5432/dataseal` | Async URL used by the FastAPI app |
| `DATABASE_URL_SYNC` | `postgresql://dataseal:dataseal@db:5432/dataseal` | Sync URL used by Celery workers and Alembic migrations |

If using an external PostgreSQL instance, update both URLs to point to it and remove the `db` service from `docker-compose.yml`.

### Valkey

| Variable | Default | Notes |
|----------|---------|-------|
| `VALKEY_URL` | `redis://localhost:6379/0` | Used as Celery broker and JWT revocation store. Uses `redis://` scheme for Celery transport compatibility. |

If using an external Valkey instance, update this URL and remove the `valkey` service from `docker-compose.yml`.

### Email (SMTP)

| Variable | Default | Notes |
|----------|---------|-------|
| `SMTP_HOST` | `localhost` | Your SMTP server hostname |
| `SMTP_PORT` | `1025` | Typically `587` for STARTTLS, `465` for TLS |
| `SMTP_USER` | `` | SMTP authentication username |
| `SMTP_PASSWORD` | `` | SMTP authentication password |
| `SMTP_FROM_ADDRESS` | `noreply@dataseal.example.com` | Sender address for all outgoing email |
| `SMTP_FROM_NAME` | `DataSeal` | Sender display name |
| `SMTP_USE_TLS` | `false` | Set to `true` for SMTP over TLS (port 465) |

**Recommended providers**: SendGrid, Mailgun, AWS SES, Postmark. For STARTTLS (port 587), configure `SMTP_PORT=587` and `SMTP_USE_TLS=false` (STARTTLS is negotiated automatically).

### Storage

| Variable | Default | Notes |
|----------|---------|-------|
| `STORAGE_BACKEND` | `local` | Only `local` is supported in this release |
| `STORAGE_LOCAL_PATH` | `/data/storage` | Path inside the container. Mounted via Docker volume. |

In production, ensure the `storage_data` Docker volume is backed by persistent storage (e.g., an EBS volume, NFS mount, or network-attached block storage). For S3-compatible storage, implement the `StorageBackend` ABC in `dataseal/storage.py`.

### Signing

| Variable | Default | Notes |
|----------|---------|-------|
| `SIGNING_TOKEN_EXPIRY_HOURS` | `72` | How long signing links remain valid after being sent |
| `MAX_DOCUMENT_SIZE_MB` | `25` | Maximum PDF upload size |
| `MAX_DOCUMENTS_PER_ENVELOPE` | `10` | Maximum PDFs per envelope |

### Auth / JWT

| Variable | Default | Notes |
|----------|---------|-------|
| `ACCESS_TOKEN_EXPIRY_MINUTES` | `15` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRY_DAYS` | `7` | JWT refresh token lifetime |

---

## Docker Compose Services

```yaml
services:
  app           # FastAPI on port 8000
  celery-worker # Background tasks (email, PDF rendering, webhooks)
  celery-beat   # Scheduled task dispatcher
  db            # PostgreSQL 16
  valkey        # Valkey 8
  mailhog       # Dev email capture (remove in production)
```

### Production adjustments

**Remove MailHog** and configure a real SMTP provider:

```yaml
# Remove this service block from docker-compose.yml for production:
  mailhog:
    image: mailhog/mailhog
    ...
```

**Remove host-exposed database ports** to prevent direct access from outside the host. In `docker-compose.yml`, remove the `ports` declarations from `db` and `valkey`:

```yaml
  db:
    image: postgres:16-alpine
    # Remove the 'ports' section below for production
    # ports:
    #   - "5432:5432"
```

**Set a Valkey password** for production deployments by adding `--requirepass <password>` to the Valkey command and updating `VALKEY_URL`:

```yaml
  valkey:
    image: valkey/valkey:8-alpine
    command: valkey-server --requirepass your-valkey-password
```

```
VALKEY_URL=redis://:your-valkey-password@valkey:6379/0
```

**Disable OpenAPI docs** in production by setting the `docs_url` and `redoc_url` to `None` in `dataseal/main.py`, or route them behind authentication at the nginx layer.

---

## Database Migrations

Migrations run automatically when the `app` container starts:

```bash
python -m alembic upgrade head
```

This is defined in the `app` service command in `docker-compose.yml`. Alembic uses `DATABASE_URL_SYNC` (the synchronous PostgreSQL URL) when running migrations.

### Running migrations manually

```bash
# Apply all pending migrations
docker compose exec app python -m alembic upgrade head

# Check current migration state
docker compose exec app python -m alembic current

# Roll back one migration
docker compose exec app python -m alembic downgrade -1

# Generate a new migration after model changes (development only)
docker compose exec app python -m alembic revision --autogenerate -m "describe the change"
```

The initial migration (`alembic/versions/001_initial_schema.py`) creates all 15 database tables with their indexes and foreign key constraints.

---

## TLS / HTTPS

DataSeal does not terminate TLS itself. Use a reverse proxy in front of the `app` container.

### nginx example

```nginx
server {
    listen 443 ssl http2;
    server_name sign.yourcompany.com;

    ssl_certificate     /etc/letsencrypt/live/sign.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sign.yourcompany.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Increase timeout for file uploads
        proxy_read_timeout 120s;
        client_max_body_size 30m;
    }
}

server {
    listen 80;
    server_name sign.yourcompany.com;
    return 301 https://$host$request_uri;
}
```

Set `APP_URL=https://sign.yourcompany.com` in `.env` after configuring TLS. This value appears in all outgoing signing links.

---

## Celery Workers

### Queues

The Celery worker consumes five queues:

| Queue | Tasks |
|-------|-------|
| `celery` | Default queue |
| `emails` | Signing invitation, completion, void, and decline emails |
| `documents` | PDF to PNG page rendering |
| `webhooks` | Webhook delivery and retry |
| `finalize` | PDF signature overlay and certificate generation |

### Scaling

To increase throughput, run multiple Celery workers or increase concurrency:

```yaml
# docker-compose.yml
  celery-worker:
    ...
    command: celery -A dataseal.tasks.celery_app worker --loglevel=info --concurrency=8 -Q celery,emails,documents,webhooks,finalize
```

Or run separate worker containers per queue for better isolation:

```bash
# Dedicated document-processing worker (CPU-bound)
docker compose run --rm -d celery-worker \
  celery -A dataseal.tasks.celery_app worker --loglevel=info --concurrency=2 -Q documents

# Dedicated webhook delivery worker
docker compose run --rm -d celery-worker \
  celery -A dataseal.tasks.celery_app worker --loglevel=info --concurrency=4 -Q webhooks
```

### Monitoring

Install Flower for real-time task monitoring:

```bash
pip install flower
celery -A dataseal.tasks.celery_app flower --port=5555
```

---

## Backup and Recovery

### PostgreSQL backup

```bash
# Create a backup
docker compose exec db pg_dump -U dataseal dataseal > backup_$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T db psql -U dataseal dataseal < backup_20260328.sql
```

### File storage backup

The `storage_data` Docker volume contains all uploaded PDFs, rendered page images, and completed documents. Back this up regularly:

```bash
# Identify the volume path on the host
docker volume inspect dataseal_storage_data

# Backup using tar
tar -czf storage_backup_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/dataseal_storage_data/_data
```

In production, consider mounting the storage volume to a managed storage service or taking periodic snapshots.

---

## Monitoring and Observability

### Health check endpoint

```bash
curl https://sign.yourcompany.com/health
```

Returns `{"status":"ok","db":"ok","valkey":"ok"}` when all dependencies are reachable. Returns `503` with `"status":"degraded"` if any dependency is unavailable. Use this endpoint for load balancer health checks.

### Logging

The application uses `structlog` (imported but not yet fully configured for structured output). Container logs are written to stdout and can be collected by any standard log aggregator:

```bash
# Follow all container logs
docker compose logs -f

# Follow only the app logs
docker compose logs -f app

# Follow Celery worker logs
docker compose logs -f celery-worker
```

---

## Security Hardening Checklist

Before going live, verify the following:

- [ ] `SECRET_KEY` is set to a cryptographically random value of at least 32 characters
- [ ] `DEBUG=false` in production
- [ ] `APP_URL` is set to the correct HTTPS URL (signing links use this)
- [ ] MailHog service is removed from `docker-compose.yml`
- [ ] PostgreSQL and Valkey `ports` are not exposed to the host
- [ ] Valkey has a password configured
- [ ] TLS is terminated at a reverse proxy; `SMTP_USE_TLS=true` if using TLS SMTP
- [ ] OpenAPI docs (`/docs`, `/redoc`) are restricted or disabled
- [ ] File storage volume is on persistent, backed-up storage
- [ ] Automatic database backups are scheduled

### Known security limitations (to address before production)

- **Rate limiting**: The `slowapi` package is a dependency but the middleware is not mounted. All endpoints are currently unthrottled. Mount `SlowAPIMiddleware` and apply the `@limiter.limit()` decorator to login, register, and signing endpoints.
- **OAuth codes**: Authorization codes are stored in Valkey with a 10-minute TTL. Ensure Valkey is available and persistent for production.
- **Content-Security-Policy**: The security headers middleware does not set a `Content-Security-Policy` header. Add a CSP appropriate for the signing page before allowing untrusted content.

---

## Upgrading

```bash
# Pull latest code
git pull

# Rebuild images
docker compose build

# Apply any new migrations and restart services
docker compose up -d

# Verify health
curl http://localhost:8000/health
```

Migrations run automatically on `app` startup. Review the `alembic/versions/` directory for any new migration files before upgrading to understand what schema changes will be applied.
