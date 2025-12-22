import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
from unittest.mock import MagicMock

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
    "matplotlib.figure",
    "pandas",
    "lxml",
    "lxml.etree",
    "onelogin",
    "onelogin.saml2",
    "onelogin.saml2.auth",
    "onelogin.saml2.settings",
    "onelogin.saml2.utils",
    "xmlsec",
]

for module in mock_modules:
    mock = MagicMock()
    mock.__spec__ = MagicMock()
    sys.modules[module] = mock

try:
    print("Importing models...")
    print("Models imported successfully!")

    from app.db.session import Base
    from sqlalchemy import create_engine

    print("Creating engine...")
    engine = create_engine("sqlite:///:memory:")

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    print("SUCCESS! All mappers configured correctly.")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
