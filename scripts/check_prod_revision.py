import os
import sys
from alembic.config import Config
from alembic import command
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def check_current_revision():
    os.environ["DATABASE_URL"] = PROD_DB_URL
    alembic_cfg = Config("alembic.ini")
    
    print("Checking current revision in PROD RDS...")
    try:
        command.current(alembic_cfg, verbose=True)
    except Exception as e:
        print(f"Error checking revision: {e}")

if __name__ == "__main__":
    check_current_revision()
