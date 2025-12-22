import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting imports...")
try:
    from main import app
    print("Imported main")
    from app.db.session import Base
    print("Imported Base")
    from app.api.deps import get_db
    print("Imported get_db")
    from app.core.security import create_access_token
    print("Imported create_access_token")
    from app.models.user import User
    print("Imported User")
    from app.models.course import Course
    print("Imported Course")
    from app.models.cart import CartItem, ShoppingCart
    print("Imported Cart models")
    from app.models.coupon import Coupon
    print("Imported Coupon")
    print("All imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
