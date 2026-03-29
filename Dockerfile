# Multi-stage build for DataSeal

# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies (poppler for pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /data/storage

# Create non-root user
RUN groupadd -r dataseal && useradd -r -g dataseal dataseal
RUN chown -R dataseal:dataseal /app /data/storage
USER dataseal

EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "dataseal.main:app", "--host", "0.0.0.0", "--port", "8000"]
