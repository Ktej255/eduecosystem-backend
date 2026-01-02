import sys
import os

# Add backend root to path
backend_path = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.insert(0, backend_path)

try:
    print("Attempting to import pdf_study...")
    from app.api.api_v1.endpoints import pdf_study
    print("pdf_study imported successfully.")

    print("Attempting to import batch1_content...")
    from app.api.api_v1.endpoints import batch1_content
    print("batch1_content imported successfully.")
    
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
