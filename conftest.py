import pytest
import os
os.environ["TESTING"] = "true"
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import time
from unittest.mock import MagicMock


# Mock optional dependencies before importing app
# This prevents ModuleNotFoundError during test collection
mock_modules = [
    "reportlab",
    "reportlab.lib",
    "reportlab.lib.pagesizes",
    "reportlab.lib.units",
    "reportlab.pdfgen",
    "reportlab.platypus",
    "reportlab.lib.styles",
    "reportlab.lib.colors",
    "reportlab.lib.enums",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.backends.backend_agg",
    "pandas",
    "lxml",
    "lxml.etree",
    "onelogin",
    "onelogin.saml2",
    "onelogin.saml2.auth",
    "onelogin.saml2.settings",
    "xmlsec",
    "redis",
    "redis.exceptions",
    "aioredis",
    "motor",
    "motor.motor_asyncio",
]
    
for module_name in mock_modules:
    if module_name not in sys.modules:
        # print(f"DEBUG: Mocking {module_name}")
        mock = MagicMock()
        mock.__spec__ = MagicMock()
        mock.__spec__.name = module_name
        if module_name == "redis":
            mock.__version__ = "4.0.0"
        sys.modules[module_name] = mock

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.base import Base
from app.api.deps import get_db
from main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.course import Course
from app.models.cart import ShoppingCart, CartItem
from app.models.coupon import Coupon

SQLALCHEMY_DATABASE_URL = f"sqlite:///./test_pytest_{int(time.time())}.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    print("DEBUG: Starting create_test_db")
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
        print("DEBUG: Tables created")
    except Exception as e:
        print(f"DEBUG: Error creating tables: {e}")
        raise e
    
    yield
    print("DEBUG: Tearing down test db")
    # Drop tables
    Base.metadata.drop_all(bind=engine)
    # Remove database file
    db_file = SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(f"./{db_file}"):
        try:
            os.remove(f"./{db_file}")
        except PermissionError:
            pass


@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    from app.core.security import get_password_hash
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),  # Hash the password "password"
        full_name="Test User",
        is_active=True,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_headers(client, test_user):
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def normal_user_token_headers(test_user):
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_course(db, test_user):
    course = Course(
        title="Test Course",
        slug="test-course",
        description="Test Description",
        instructor_id=test_user.id,
        price=100.0,
        is_published=True,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@pytest.fixture(scope="function")
def test_cart_item(db, test_user, test_course):
    cart = ShoppingCart(user_id=test_user.id)
    db.add(cart)
    db.commit()

    item = CartItem(
        cart_id=cart.id,
        course_id=test_course.id,
        quantity=1,
        unit_price=test_course.price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture(scope="function")
def test_coupon(db, test_user):
    coupon = Coupon(
        code="TESTCOUPON",
        discount_type="percentage",
        discount_value=10.0,
        is_active=True,
        instructor_id=test_user.id,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@pytest.fixture(scope="function")
def superuser_token_headers(db):
    admin = User(
        email="admin@test.com",
        hashed_password="hashedpassword",
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    access_token = create_access_token(subject=admin.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_cart_with_items(db, test_user, test_course):
    """Shopping cart with course items for order tests"""
    cart = ShoppingCart(user_id=test_user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)

    # Add cart item
    item = CartItem(
        cart_id=cart.id,
        course_id=test_course.id,
        quantity=1,
        unit_price=test_course.price,
    )
    db.add(item)
    db.commit()

    return cart


@pytest.fixture(scope="function")
def test_empty_cart(db, test_user):
    """Empty shopping cart for order tests"""
    cart = ShoppingCart(user_id=test_user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


@pytest.fixture(scope="function")
def test_completed_order(db, test_user, test_course):
    """Completed order for order management tests"""
    from app.models.order import Order, OrderItem, OrderStatus

    order = Order(
        order_number=Order.generate_order_number(),
        user_id=test_user.id,
        status=OrderStatus.COMPLETED,
        subtotal=test_course.price,
        total=test_course.price,
        currency="USD",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Add order item
    item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        quantity=1,
        unit_price=test_course.price,
        total=test_course.price,
    )
    db.add(item)
    db.commit()

    return order


# Additional user and token fixtures
@pytest.fixture(scope="function")
def normal_user(db):
    """Normal non-superuser for subscription/tax/2FA tests"""
    user = User(
        email="normal@test.com",
        hashed_password="hashedpassword",
        full_name="Normal User",
        is_active=True,
        is_superuser=False,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_token_headers(normal_user):
    """Token headers for normal_user"""
    access_token = create_access_token(subject=normal_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def other_user_token_headers(db):
    """Token headers for a different user (for access control tests)"""
    other_user = User(
        email="other@test.com",
        hashed_password="hashedpassword",
        full_name="Other User",
        is_active=True,
        is_superuser=False,
        role="student",
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    access_token = create_access_token(subject=other_user.id)
    return {"Authorization": f"Bearer {access_token}"}


# Order fixtures
@pytest.fixture(scope="function")
def test_pending_order(db, test_user, test_course):
    """Pending order for order workflow tests"""
    from app.models.order import Order, OrderItem, OrderStatus

    order = Order(
        order_number=Order.generate_order_number(),
        user_id=test_user.id,
        status=OrderStatus.PENDING,
        subtotal=test_course.price,
        total=test_course.price,
        currency="USD",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        quantity=1,
        unit_price=test_course.price,
        total=test_course.price,
    )
    db.add(item)
    db.commit()

    return order


@pytest.fixture(scope="function")
def test_pending_order_with_courses(db, test_user, test_course):
    """Pending order with courses for enrollment creation tests"""
    from app.models.order import Order, OrderItem, OrderStatus

    order = Order(
        order_number=Order.generate_order_number(),
        user_id=test_user.id,
        status=OrderStatus.PENDING,
        subtotal=test_course.price,
        total=test_course.price,
        currency="USD",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        quantity=1,
        unit_price=test_course.price,
        total=test_course.price,
    )
    db.add(item)
    db.commit()

    return order


@pytest.fixture(scope="function")
def test_order(db, test_user, test_course):
    """Generic order fixture (alias for test_completed_order)"""
    from app.models.order import Order, OrderItem, OrderStatus

    order = Order(
        order_number=Order.generate_order_number(),
        user_id=test_user.id,
        status=OrderStatus.COMPLETED,
        subtotal=test_course.price,
        total=test_course.price,
        currency="USD",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        quantity=1,
        unit_price=test_course.price,
        total=test_course.price,
    )
    db.add(item)
    db.commit()

    return order


@pytest.fixture(scope="function")
def test_guest_order(db, test_course):
    """Guest order (order without user_id) for guest checkout tests"""
    from app.models.order import Order, OrderItem, OrderStatus

    order = Order(
        order_number=Order.generate_order_number(),
        guest_email="guest@test.com",
        status=OrderStatus.PENDING,
        subtotal=test_course.price,
        total=test_course.price,
        currency="USD",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        quantity=1,
        unit_price=test_course.price,
        total=test_course.price,
    )
    db.add(item)
    db.commit()

    return order
