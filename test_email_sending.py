import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.getcwd())

from app.core.email import send_email
from app.core.config import settings


async def test_send_email():
    print(f"Testing email sending with SUPPRESS_SEND={settings.MAIL_SUPPRESS_SEND}")
    try:
        await send_email(
            email_to="test@example.com",
            subject="Test Email",
            template_name="welcome.html",
            template_body={
                "name": "Test User",
                "dashboard_url": "http://localhost:3000/dashboard",
            },
        )
        print("✅ Email sending function executed successfully (suppressed).")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_send_email())
