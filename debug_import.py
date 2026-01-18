import sys
import traceback

sys.path.append(".")

try:
    print("Attempting to import api_router...")
    from app.api.api_v1.api import api_router
    print(f"Success! Routes: {len(api_router.routes)}")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
