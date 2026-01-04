
try:
    from app.api.api_v1.endpoints import pdf_study
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
