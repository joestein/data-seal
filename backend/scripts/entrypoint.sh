#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting DataSeal..."
exec uvicorn dataseal.main:app --host 0.0.0.0 --port 8000
