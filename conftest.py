import sys
import os

# Set testing environment variable to prevent startup hangs (lifespan)
os.environ["TESTING"] = "true"

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add the backend root to sys.path to resolve "app" module
# Add the backend root to sys.path to resolve "app" module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock reportlab to avoid dependency issues during tests
# Must mock ALL submodules before any imports happen
from unittest.mock import MagicMock

# Create a proper mock package structure
_reportlab_mock = MagicMock()
_reportlab_lib_mock = MagicMock()
_reportlab_platypus_mock = MagicMock()

sys.modules["reportlab"] = _reportlab_mock
sys.modules["reportlab.pdfgen"] = MagicMock()
sys.modules["reportlab.pdfgen.canvas"] = MagicMock()
sys.modules["reportlab.lib"] = _reportlab_lib_mock
sys.modules["reportlab.lib.pagesizes"] = MagicMock()
sys.modules["reportlab.lib.units"] = MagicMock()
sys.modules["reportlab.lib.colors"] = MagicMock()
sys.modules["reportlab.lib.styles"] = MagicMock()
sys.modules["reportlab.lib.enums"] = MagicMock()
sys.modules["reportlab.platypus"] = _reportlab_platypus_mock
sys.modules["reportlab.platypus.paragraph"] = MagicMock()
sys.modules["reportlab.platypus.tables"] = MagicMock()
sys.modules["reportlab.platypus.flowables"] = MagicMock()

# Mock google-generativeai to avoid quota issues and network calls
_genai_mock = MagicMock()
_genai_model_mock = MagicMock()
_genai_mock.GenerativeModel.return_value = _genai_model_mock
_genai_model_mock.generate_content.return_value.text = "Mock AI response"
_genai_mock.embed_content.return_value = {"embedding": [[0.1] * 768]}

sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = _genai_mock
sys.modules["google.generativeai.types"] = MagicMock()

from main import app
from app.db.session import SessionLocal, engine
from app.api.deps import get_db
from app.models.course import Course
from app.models.user import User
from app.models.cart import ShoppingCart, CartItem
from app.models.coupon import Coupon
from app.tests.utils.course import create_random_course
from app.tests.utils.utils import random_lower_string
from app.tests.utils.user import create_random_user

# Use a test database URL - distinct for safety
# We'll use the default for now but ideally it should be a test-specific one
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_final_debug.db"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    # Create tables
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)
    
    # Manually add is_verified column if it doesn't exist (SQLAlchemy sometimes misses this in tests)
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass  # Column already exists
            
    yield engine
    # Cleanup (optional)
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine) -> Generator:
    connection = db_engine.connect()
    transaction = connection.begin()
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db: Session) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_course(db: Session) -> Course:
    return create_random_course(db)

@pytest.fixture
def normal_user(db: Session) -> User:
    """Standard student user for tests"""
    from app.core.security import get_password_hash
    from app.tests.utils.utils import random_lower_string
    
    suffix = random_lower_string()
    user = User(
        email=f"normal_user_{suffix}@example.com",
        username=f"normal_user_{suffix}",
        hashed_password=get_password_hash("testpassword"),
        full_name="Normal User",
        is_active=True,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"DEBUG: Created normal_user with ID {user.id} and email {user.email}")
    return user

@pytest.fixture
def test_cart_with_items(db: Session, test_course: Course, normal_user: User) -> ShoppingCart:
    cart = ShoppingCart(user_id=normal_user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    print(f"DEBUG: Created cart {cart.id} for normal_user {normal_user.id}")
    
    cart_item = CartItem(
        cart_id=cart.id, 
        course_id=test_course.id, 
        unit_price=test_course.price or 0.0,
        quantity=1
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart)
    return cart

@pytest.fixture
def test_cart_item(db: Session, test_cart_with_items: ShoppingCart) -> CartItem:
    return test_cart_with_items.items[0]

@pytest.fixture
def test_user(db: Session):
    """Create a standard test user"""
    from app.core.security import get_password_hash
    from app.models.user import User
    
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def normal_user_token_headers(client: TestClient, normal_user: User) -> dict:
    """Get authentication headers for a normal user"""
    # Login to get token
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": normal_user.email, "password": "testpassword"},
    )
    token = response.json().get("access_token")
    print(f"DEBUG: Obtained token for normal_user {normal_user.id} ({normal_user.email})")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_headers(normal_user_token_headers: dict) -> dict:
    """Alias for normal_user_token_headers, used by some tests"""
    return normal_user_token_headers

@pytest.fixture
def superuser_token_headers(client: TestClient, db: Session) -> dict:
    """Get authentication headers for a superuser"""
    from app.core.security import get_password_hash
    from app.models.user import User
    
    # Create superuser
    user = User(
        email="superuser@example.com",
        username="superuser",
        hashed_password=get_password_hash("superpassword"),
        full_name="Super User",
        is_active=True,
        is_superuser=True,
        role="admin",
    )
    db.add(user)
    db.commit()
    
    # Login to get token
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "superuser@example.com", "password": "superpassword"},
    )
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_user_token_headers(client: TestClient, db: Session) -> dict:
    """Get authentication headers for another user (for testing access control)"""
    from app.core.security import get_password_hash
    from app.models.user import User
    
    user = User(
        email="other_user@example.com",
        username="other_user",
        hashed_password=get_password_hash("otherpassword"),
        full_name="Other User",
        is_active=True,
        role="student",
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "other_user@example.com", "password": "otherpassword"},
    )
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_empty_cart(db: Session, normal_user: User) -> ShoppingCart:
    """Create an empty shopping cart for normal user"""
    cart = ShoppingCart(user_id=normal_user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

@pytest.fixture
def test_coupon(db: Session, test_course: Course, normal_user: User) -> Coupon:
    """Create a test coupon"""
    from datetime import datetime, timedelta
    from app.tests.utils.utils import random_lower_string
    
    code = f"TESTCOUPON_{random_lower_string()}"
    coupon = Coupon(
        code=code,
        discount_type="percentage",
        discount_value=10.0,
        is_active=True,
        valid_from=datetime.utcnow() - timedelta(days=1),
        valid_until=datetime.utcnow() + timedelta(days=7),
        instructor_id=normal_user.id,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@pytest.fixture
def test_order(db: Session, normal_user: User):
    """Create a test order for normal user"""
    from app.models.order import Order, OrderStatus
    
    order = Order(
        user_id=normal_user.id,
        order_number="ORD-TEST-123456",
        status=OrderStatus.COMPLETED,
        total=999.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@pytest.fixture
def test_pending_order(db: Session, normal_user: User):
    """Create a pending test order for normal user"""
    from app.models.order import Order, OrderStatus
    
    order = Order(
        user_id=normal_user.id,
        order_number="ORD-PENDING-123",
        status=OrderStatus.PENDING,
        total=500.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@pytest.fixture
def test_completed_order(db: Session, normal_user: User):
    """Create a completed test order for normal user"""
    from app.models.order import Order, OrderStatus
    
    order = Order(
        user_id=normal_user.id,
        order_number="ORD-COMPLETED-123",
        status=OrderStatus.COMPLETED,
        total=1500.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@pytest.fixture
def test_pending_order_with_courses(db: Session, test_course: Course, normal_user: User):
    """Create a pending order with course items for normal user"""
    from app.models.order import Order, OrderStatus, OrderItem
    
    order = Order(
        user_id=normal_user.id,
        order_number="ORD-COURSES-123",
        status=OrderStatus.PENDING,
        total=test_course.price or 0,
    )
    db.add(order)
    db.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        course_id=test_course.id,
        item_name=test_course.title,
        unit_price=test_course.price or 0.0,
        total=test_course.price or 0.0,
    )
    db.add(order_item)
    db.commit()
    db.refresh(order)
    return order

@pytest.fixture
def test_guest_order(db: Session):
    """Create a guest order"""
    from app.models.order import Order, OrderStatus
    
    order = Order(
        order_number="ORD-GUEST-123",
        status=OrderStatus.PENDING,
        total=750.0,
        guest_email="guest@example.com",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
