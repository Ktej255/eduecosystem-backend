#!/bin/bash
set -e

echo "Running Database Migrations..."
alembic upgrade head

echo "Starting Application..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
