import sys
import os

print("Testing Backend Setup...")

# Add project root to sys.path to allow imports from 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming this script is in backend/
sys.path.append(current_dir)

try:
    print("1. Importing easyocr...")
    import easyocr
    print("   SUCCESS: easyocr imported.")
except ImportError as e:
    print(f"   FAIL: easyocr import failed: {e}")
    print("   Run: pip install -r requirements.txt")

try:
    print("2. Importing google.generativeai...")
    import google.generativeai as genai
    print("   SUCCESS: google.generativeai imported.")
except ImportError as e:
    print(f"   FAIL: google.generativeai import failed: {e}")

try:
    print("3. Checking app services...")
    from app.services.ocr import analyze_handwriting
    from app.services.gemini_service import gemini_service
    print("   SUCCESS: App services imported.")
except ImportError as e:
    print(f"   FAIL: App imports failed: {e}")
    print(f"   Current sys.path: {sys.path}")

print("\nSetup verification check finished.")
