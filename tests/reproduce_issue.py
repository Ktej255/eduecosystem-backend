from app.db.session import Base
from sqlalchemy import create_engine


def test_model_init():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    print("Models initialized successfully!")
