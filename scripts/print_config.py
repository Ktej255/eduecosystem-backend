import os
import sys

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.core.config import settings

def print_config():
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"DATABASE_URL (sanitized): {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"POSTGRES_DB: {settings.POSTGRES_DB}")

if __name__ == "__main__":
    print_config()
