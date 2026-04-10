import sys
import os
import time

sys.path.insert(0, '/app')
os.environ["TESTING"] = "true"

import logging
logging.getLogger("passlib").setLevel(logging.ERROR)

from unittest.mock import MagicMock
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.generativeai.types"] = MagicMock()

import pyotp

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup database in memory to avoid all the complex model initialization issues of main.py
engine = create_engine('sqlite:///:memory:', echo=False)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

from app.db.base_class import Base
from app.models.cart import ShoppingCart, CartItem
from app.models.course import Course
from app.models.bundle import CourseBundle
from app.models.coupon import Coupon
from app.models.order import Order, OrderItem
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate

# We will patch the model loading.
# First, create tables just for models we need.
ShoppingCart.__table__.create(engine)
CartItem.__table__.create(engine)
Course.__table__.create(engine)
CourseBundle.__table__.create(engine)
Coupon.__table__.create(engine)
Order.__table__.create(engine)
OrderItem.__table__.create(engine)

def main():
    print("Setting up data...")

    courses = []
    for i in range(100):
        c = Course(id=i+1, title=f"Course {i}", description=f"Desc {i}", price=10.0, is_published=True)
        db.add(c)
        courses.append(c)

    bundle = CourseBundle(id=1, name="Test Bundle", description="Bundle desc", price=50.0)
    db.add(bundle)

    coupon = Coupon(id=1, code="DISCOUNT10", discount_amount=10.0, is_active=True)
    db.add(coupon)

    db.commit()

    cart = ShoppingCart(id=1, user_id=1)
    db.add(cart)
    db.commit()

    for c in courses:
        ci = CartItem(cart_id=cart.id, course_id=c.id, unit_price=c.price, quantity=1, total=c.price, discount_amount=0)
        db.add(ci)

    db.commit()

    order_data = OrderCreate(
        billing_name="Test",
        billing_email="test@test.com",
        billing_address="Test Address"
    )

    from sqlalchemy import event
    query_count = [0]

    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if "INSERT" not in statement and "UPDATE" not in statement and "DELETE" not in statement and "BEGIN" not in statement and "COMMIT" not in statement:
            query_count[0] += 1

    print("Running baseline profiling...")
    start_time = time.time()
    order = OrderService.create_order_from_cart(db, cart.id, order_data, user_id=1)
    end_time = time.time()

    print(f"Time taken to create order from cart with 100 items: {end_time - start_time:.4f} seconds")
    print(f"Total SELECT queries executed: {query_count[0]}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
