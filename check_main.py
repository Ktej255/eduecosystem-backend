
try:
    from app import main
    print("Import main successful")
except Exception as e:
    print(f"Import main failed: {e}")
    import traceback
    traceback.print_exc()
