#!/bin/bash
# Production startup script with timeout protection
# Prevents container hanging when database is unreachable

echo "Starting Eduecosystem Backend..."

# Skip migrations on startup to prevent timeout hangs
# Migrations should be run manually when needed:
#   docker exec <container> alembic upgrade head
# Or via a separate migration job
echo "Skipping automatic migrations (run manually when needed)"

echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30
