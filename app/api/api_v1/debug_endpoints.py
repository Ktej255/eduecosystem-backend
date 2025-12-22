import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

print("Starting endpoint imports...")
try:
    print("Importing auth...")
    from app.api.api_v1.endpoints import auth
    print("Importing users...")
    from app.api.api_v1.endpoints import users
    print("Importing ai...")
    from app.api.api_v1.endpoints import ai
    print("Importing upload...")
    from app.api.api_v1.endpoints import upload
    print("Importing notifications...")
    from app.api.api_v1.endpoints import notifications
    print("Importing social...")
    from app.api.api_v1.endpoints import social
    print("Importing courses...")
    from app.api.api_v1.endpoints import courses
    print("Importing live_classes...")
    from app.api.api_v1.endpoints import live_classes
    print("Importing chat...")
    from app.api.api_v1.endpoints import chat
    print("Importing two_factor...")
    from app.api.api_v1.endpoints import two_factor
    print("All endpoint imports successful")
except Exception as e:
    print(f"Endpoint import failed: {e}")
    import traceback
    traceback.print_exc()
