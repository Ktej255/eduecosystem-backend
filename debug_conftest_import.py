try:
    import conftest
    print("Conftest imported successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
