#!/bin/bash
# Production startup script with timeout protection
# Prevents container hanging when database is unreachable

echo "Starting Eduecosystem Backend..."

# Run migrations on startup to ensure schema is up to date
echo "Running automatic migrations..."
alembic upgrade head

echo "Starting uvicorn server..."
# Run the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30
