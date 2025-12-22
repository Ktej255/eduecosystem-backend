import sys
import os
sys.path.append(os.getcwd())

import pydantic
import fastapi
print(f"Pydantic version: {pydantic.VERSION}")
try:
    print("Importing main app...")
    from main import app
    print("Success importing main app")
    
    print("Registered Routes:")
    for route in app.routes:
        if hasattr(route, "path") and ("daily-actions" in route.path or "admin/drill" in route.path):
            print(f"  {route.path} {route.methods}")
            
except Exception as e:
    print(f"Failed to import main app: {e}")
    import traceback
    traceback.print_exc()
