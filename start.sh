#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || echo "Migration failed or already applied"

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
