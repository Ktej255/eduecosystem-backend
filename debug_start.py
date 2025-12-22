import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")
print(f"Files in CWD: {os.listdir('.')}")

try:
    import app
    print(f"App module: {app}")
    if hasattr(app, '__file__'):
        print(f"App file: {app.__file__}")
    
    import app.main
    print("Successfully imported app.main")
except Exception as e:
    import traceback
    traceback.print_exc()
