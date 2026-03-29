"""FastAPI application factory and configuration."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dataseal.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DataSeal",
        description="Electronic Signature and Agreement Management Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [settings.app_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Health check
    @app.get("/health")
    async def health_check():
        health = {"status": "ok"}

        # Check database
        try:
            from sqlalchemy import text

            from dataseal.database import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health["db"] = "ok"
        except Exception:
            health["db"] = "error"
            health["status"] = "degraded"

        # Check Valkey
        try:
            import valkey

            r = valkey.from_url(settings.valkey_url)
            r.ping()
            health["valkey"] = "ok"
        except Exception:
            health["valkey"] = "error"
            health["status"] = "degraded"

        status_code = 200 if health["status"] == "ok" else 503
        return JSONResponse(content=health, status_code=status_code)

    # Mount API routers
    from dataseal.api.auth import router as auth_router
    from dataseal.api.documents import router as documents_router
    from dataseal.api.envelopes import router as envelopes_router
    from dataseal.api.fields import router as fields_router
    from dataseal.api.oauth import router as oauth_router
    from dataseal.api.powerforms import router as powerforms_router
    from dataseal.api.recipients import router as recipients_router
    from dataseal.api.signing import router as signing_router
    from dataseal.api.templates import router as templates_router
    from dataseal.api.webhooks import router as webhooks_router

    api_prefix = "/api/v1"

    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(envelopes_router, prefix=api_prefix)
    app.include_router(documents_router, prefix=api_prefix)
    app.include_router(recipients_router, prefix=api_prefix)
    app.include_router(fields_router, prefix=api_prefix)
    app.include_router(signing_router, prefix=api_prefix)
    app.include_router(templates_router, prefix=api_prefix)
    app.include_router(powerforms_router, prefix=api_prefix)
    app.include_router(webhooks_router, prefix=api_prefix)
    app.include_router(oauth_router, prefix=api_prefix)

    return app


app = create_app()
