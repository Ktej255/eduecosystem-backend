import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

try:
    import app.models

    print("Imported app.models")
    print(f"app.models has Coupon: {hasattr(app.models, 'Coupon')}")
    if hasattr(app.models, "Coupon"):
        print(app.models.Coupon)
    else:
        print("Dir of app.models:", dir(app.models))
except Exception as e:
    print(f"Error: {e}")
