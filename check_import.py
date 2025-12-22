import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.models.chat...")
    import app.models.chat

    print(f"app.models.chat imported: {app.models.chat}")

    print("Attempting to import PresenceStatus...")
    from app.models.chat import PresenceStatus

    print(f"PresenceStatus imported: {PresenceStatus}")
    print("✅ Import successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
