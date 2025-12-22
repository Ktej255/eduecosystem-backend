"""
Script to manually create email notification tables
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import engine
from app.models.email_notification import UserEmailPreference, EmailTemplate, EmailLog

if __name__ == "__main__":
    print("Creating email notification tables...")

    # Create only the email notification tables
    UserEmailPreference.__table__.create(bind=engine, checkfirst=True)
    EmailTemplate.__table__.create(bind=engine, checkfirst=True)
    EmailLog.__table__.create(bind=engine, checkfirst=True)

    print("✅ Email notification tables created successfully!")
