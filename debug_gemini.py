import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("Importing gemini_service...")
try:
    from app.services.gemini_service import gemini_service
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
