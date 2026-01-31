# Production Dockerfile for Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (libffi-dev needed for bcrypt)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
# Copy requirements first for better caching
COPY requirements.txt .

# Install CPU-only torch to prevent massive downloads/timeouts (required by easyocr)
RUN pip install --no-cache-dir --default-timeout=1000 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements with increased timeout
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run migrations and start app
# NOTE: Removed 'alembic upgrade head' from startup to prevent container hanging
# when database is unreachable. Run migrations separately when needed.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "30"]
