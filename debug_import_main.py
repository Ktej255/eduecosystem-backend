import sys
import traceback

try:
    from main import app
    print("Success: Imported app from main")
except Exception:
    with open("import_error.txt", "w") as f:
        traceback.print_exc(file=f)
    print("Failed: Check import_error.txt")
