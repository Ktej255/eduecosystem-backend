import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.models import *  # Import all models to trigger mapper initialization

    print("Attempting to configure mappers...")
    from sqlalchemy.orm import configure_mappers

    configure_mappers()
    print("Mappers configured successfully.")

except Exception:
    import traceback

    traceback.print_exc()
