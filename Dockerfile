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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
