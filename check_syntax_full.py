
try:
    print("Checking pdf_study...")
    from app.api.api_v1.endpoints import pdf_study
    print("✅ pdf_study imported")

    print("Checking batch1_content...")
    from app.api.api_v1.endpoints import batch1_content
    print("✅ batch1_content imported")

    print("Checking app.api.api_v1.api...")
    from app.api.api_v1 import api
    print("✅ api imported")

    print("Checking app.main...")
    from app import main
    print("✅ main imported")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
