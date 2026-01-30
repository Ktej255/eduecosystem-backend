import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.base import Base

def test_debug_tables(client: TestClient, db: Session):
    print(f"\nFATAL DEBUG: Tables in metadata: {list(Base.metadata.tables.keys())}")
    assert "development_logs" in Base.metadata.tables
