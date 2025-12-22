import uvicorn
import sys
import os

print(f"CWD: {os.getcwd()}")
sys.path.append(os.getcwd())

try:
    print("Starting uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
