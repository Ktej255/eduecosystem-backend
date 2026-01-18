"""
Deep diagnostic to find the specific model causing SQLAlchemy InvalidRequestError.
"""
import sys
import traceback

sys.path.append(".")

# Try importing models one by one
import os

models_dir = "app/models"
files = sorted([f for f in os.listdir(models_dir) if f.endswith(".py") and f != "__init__.py"])

print(f"Found {len(files)} model files to test...\n")

for f in files:
    module_name = f"app.models.{f[:-3]}"
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        print(f"✗ {module_name}")
        print(f"  ERROR: {e}")
        traceback.print_exc()
        print("-" * 50)
        break  # Stop at first failure to see full trace

print("\nNow attempting full api_router import...")
try:
    from app.api.api_v1.api import api_router
    print(f"SUCCESS! Routes: {len(api_router.routes)}")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
