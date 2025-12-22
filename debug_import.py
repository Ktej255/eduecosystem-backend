import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

print("Importing app.schemas.upsc...")
try:
    from app.schemas import upsc
    print("Success importing schemas!")
except Exception as e:
    print(f"Error importing schemas: {e}")
    import traceback
    traceback.print_exc()

print("\nImporting app.models.upsc...")
try:
    from app.models import upsc
    print("Success importing models!")
except Exception as e:
    print(f"Error importing models: {e}")
    import traceback
    traceback.print_exc()
