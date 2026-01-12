import sys
import os
sys.path.append(os.getcwd())
try:
    print("Attempting to import app.api.api_v1.api")
    from app.api.api_v1 import api
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
    import traceback
    traceback.print_exc()
