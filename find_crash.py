import os
import sys

# Ensure backend directory is in path
sys.path.append(os.getcwd())

endpoints_dir = "app/api/api_v1/endpoints"
files = [f for f in os.listdir(endpoints_dir) if f.endswith(".py") and f != "__init__.py"]

for f in files:
    module_name = f"app.api.api_v1.endpoints.{f[:-3]}"
    print(f"Testing {module_name}...")
    try:
        __import__(module_name)
    except Exception as e:
        print(f"FAILED: {module_name}")
        import traceback
        traceback.print_exc()
        print("-" * 50)
print("Done testing all endpoints.")
