import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import asyncio
from functools import wraps

import sys

# Pre-import mocks to ensure python successfully parses the file.
# The previous version used sys.modules modification correctly but global imports failed first.
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi_mail'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.sql'] = MagicMock()
sys.modules['motor'] = MagicMock()
sys.modules['motor.motor_asyncio'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['pydantic_settings'] = MagicMock()
sys.modules['pydantic_settings.BaseSettings'] = MagicMock()
sys.modules['app.models.lead'] = MagicMock()
sys.modules['app.core.email'] = MagicMock()

class LeadMockClass(MagicMock):
    drip_day_sent = MagicMock()
    drip_day_sent.__lt__.return_value = True

sys.modules['app.models.lead'].Lead = LeadMockClass

from app.services.drip_service import process_email_drips, DRIP_EMAILS

# Restore sys.modules so we don't break other tests in the suite.
# However, for this isolated file we'll just use a fixture to clean up afterwards.
@pytest.fixture(autouse=True, scope="module")
def cleanup_sys_modules():
    yield
    modules_to_del = [
        'fastapi', 'fastapi_mail', 'sqlalchemy', 'sqlalchemy.orm', 'sqlalchemy.sql',
        'motor', 'motor.motor_asyncio', 'pydantic', 'pydantic_settings',
        'pydantic_settings.BaseSettings',
        'app.models.lead', 'app.core.email'
    ]
    for mod in modules_to_del:
        if mod in sys.modules:
            del sys.modules[mod]

def async_to_sync(async_func):
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return wrapper

class MockLead:
    def __init__(self):
        self.created_at = None
        self.drip_day_sent = 0
        self.email = None
        self.name = None

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

@async_to_sync
async def test_no_eligible_leads(mock_db):
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}
    mock_db.commit.assert_called_once()

@async_to_sync
async def test_lead_missing_created_at(mock_db):
    lead = MockLead()
    lead.created_at = None
    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_not_enough_days_passed(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 2, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 2, tzinfo=timezone.utc)
    lead.drip_day_sent = 0
    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}
    mock_send_email.assert_not_called()

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_timezone_unaware_created_at(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 2, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1) # Unaware
    lead.drip_day_sent = 0
    lead.email = "test@example.com"
    lead.name = "Test Lead"

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 1}
    mock_send_email.assert_called_once()
    assert lead.drip_day_sent == 1
    mock_db.add.assert_called_once_with(lead)

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_send_day_1_email(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 2, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead.drip_day_sent = 0
    lead.email = "test@example.com"
    lead.name = "Test Lead"

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 1}
    mock_send_email.assert_called_once_with(
        email_to=lead.email,
        subject=DRIP_EMAILS[1]["subject"],
        template_name=DRIP_EMAILS[1]["template"],
        template_body={"name": lead.name, "body": DRIP_EMAILS[1]["body"]}
    )
    assert lead.drip_day_sent == 1

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_send_day_2_email(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 3, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead.drip_day_sent = 1
    lead.email = "test@example.com"
    lead.name = "Test Lead"

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 1}
    mock_send_email.assert_called_once_with(
        email_to=lead.email,
        subject=DRIP_EMAILS[2]["subject"],
        template_name=DRIP_EMAILS[2]["template"],
        template_body={"name": lead.name, "body": DRIP_EMAILS[2]["body"]}
    )
    assert lead.drip_day_sent == 2

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_email_send_failure(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 2, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    mock_send_email.side_effect = Exception("SMTP Error")

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead.drip_day_sent = 0
    lead.email = "test@example.com"
    lead.name = "Test Lead"

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}
    mock_send_email.assert_called_once()
    assert lead.drip_day_sent == 0 # Should not be updated
    mock_db.add.assert_not_called()

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_no_email_address(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 2, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead.drip_day_sent = 0
    lead.email = None # No email address

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}
    mock_send_email.assert_not_called()

@patch('app.services.drip_service.datetime')
@patch('app.services.drip_service.send_email', new_callable=AsyncMock)
@async_to_sync
async def test_drip_exceeds_5_days(mock_send_email, mock_datetime, mock_db):
    now = datetime(2023, 1, 10, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now

    lead = MockLead()
    lead.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead.drip_day_sent = 5
    lead.email = "test@example.com"

    mock_db.query.return_value.filter.return_value.all.return_value = [lead]

    result = await process_email_drips(mock_db)

    assert result == {"status": "success", "emails_dispatched": 0}
    mock_send_email.assert_not_called()
