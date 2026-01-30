import sys
import os
sys.path.append(os.getcwd())

print("Attempting to import DevelopmentLog...")
try:
    from app.models.development_history import DevelopmentLog
    print("SUCCESS: Imported DevelopmentLog")
except Exception as e:
    print(f"FAILED: {e}")
