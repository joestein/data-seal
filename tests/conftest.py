"""Shared test fixtures and configuration.

Approach:
- Override SQLAlchemy's type compilation for SQLite so PostgreSQL-specific types
  (INET, JSONB, UUID) map to TEXT/JSON.
- This lets us use in-memory SQLite for all API/integration tests without
  changing any production code.
"""

import os

# Must be set before dataseal.config is imported (module-level Settings instantiation)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-must-be-at-least-32-chars")
os.environ.setdefault("BCRYPT_ROUNDS", "4")

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, Text, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _setup_sqlite_type_compatibility():
    """Register event listeners to compile PG-specific types for SQLite."""
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    from sqlalchemy.dialects.postgresql import INET, JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID

    # Make INET render as TEXT
    if not hasattr(SQLiteTypeCompiler, "_visit_INET_original"):
        SQLiteTypeCompiler._visit_INET_original = True

        def visit_INET(self, type_, **kwargs):
            return "TEXT"

        SQLiteTypeCompiler.visit_INET = visit_INET

    # Make JSONB render as JSON (TEXT in sqlite)
    if not hasattr(SQLiteTypeCompiler, "_visit_JSONB_original"):
        SQLiteTypeCompiler._visit_JSONB_original = True

        def visit_JSONB(self, type_, **kwargs):
            return "JSON"

        SQLiteTypeCompiler.visit_JSONB = visit_JSONB

    # UUID already has a generic type that SQLite handles as VARCHAR


_setup_sqlite_type_compatibility()


def _get_sqlite_metadata():
    """Return Base.metadata with all models imported."""
    # Import models to ensure they are registered with Base
    import dataseal.models.user  # noqa
    import dataseal.models.envelope  # noqa
    import dataseal.models.document  # noqa
    import dataseal.models.recipient  # noqa
    import dataseal.models.field  # noqa
    import dataseal.models.audit  # noqa
    import dataseal.models.template  # noqa
    import dataseal.models.webhook  # noqa
    import dataseal.models.powerform  # noqa
    import dataseal.models.oauth  # noqa
    from dataseal.models.base import Base
    return Base.metadata


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an in-memory SQLite async engine and create all tables once per session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    metadata = _get_sqlite_metadata()

    async with engine.begin() as conn:
        # sqlite doesn't support partial indexes with WHERE clauses —
        # filter those out before creating tables
        _strip_pg_partial_indexes(metadata)
        await conn.run_sync(metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()


def _strip_pg_partial_indexes(metadata):
    """Remove PostgreSQL-specific partial index conditions that SQLite can't handle."""
    from sqlalchemy import Index
    from sqlalchemy.dialects.postgresql import ExcludeConstraint
    for table in metadata.tables.values():
        to_remove = []
        for constraint in list(table.constraints):
            # Keep only standard constraints
            pass
        for idx in list(table.indexes):
            # Remove indexes that have postgresql_where or other pg-only kwargs
            # SQLAlchemy stores dialect-specific kwargs in index.dialect_kwargs
            if any(k.startswith("postgresql_") for k in idx.dialect_kwargs):
                # Replace with a simple non-partial version
                new_cols = list(idx.columns)
                table.indexes.discard(idx)
                if new_cols:
                    new_idx = Index(idx.name, *new_cols)


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Transactional session that rolls back after each test."""
    connection = await async_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="function")
def app(db_session):
    """FastAPI test app with DB dependency overridden."""
    import os
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-must-be-at-least-32-chars"
    os.environ["BCRYPT_ROUNDS"] = "4"

    from dataseal.database import get_db
    from dataseal.main import create_app

    test_app = create_app()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.fixture(scope="function")
def client(app):
    """Synchronous TestClient with all Celery tasks mocked out."""
    with (
        patch("dataseal.tasks.emails.send_signing_emails.delay", return_value=None),
        patch("dataseal.tasks.emails.send_void_notification.delay", return_value=None),
        patch("dataseal.tasks.emails.send_decline_notification.delay", return_value=None),
        patch("dataseal.tasks.emails.send_completion_emails.delay", return_value=None),
        patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay", return_value=None),
        patch("dataseal.tasks.webhooks.deliver_webhook.delay", return_value=None),
        patch("dataseal.tasks.finalize.finalize_envelope.delay", return_value=None),
        patch("dataseal.tasks.documents.render_document_pages.delay", return_value=None),
        patch("dataseal.api.webhooks.validate_webhook_url", side_effect=lambda url: url),
    ):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ---- Auth helpers ----

@pytest.fixture
def registered_user(client):
    """Register a test user and return the profile JSON."""
    response = client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "company": "Test Corp",
    })
    assert response.status_code == 201, response.json()
    return response.json()


@pytest.fixture
def auth_token(client, registered_user):
    """Return a JWT access token for the registered test user."""
    response = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "TestPass123!",
    })
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return Bearer auth header dict."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def second_user_auth(client):
    """Register a second user and return their auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": "second@example.com",
        "password": "SecondPass123!",
        "full_name": "Second User",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "second@example.com",
        "password": "SecondPass123!",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
