import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from app.services.payout_service import PayoutService
import os

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("PAYPAL_MODE", "sandbox")

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_get_paypal_access_token_success(mock_post, mock_env):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_access_token"}
    mock_post.return_value = mock_response

    token = await PayoutService._get_paypal_access_token()

    assert token == "test_access_token"
    mock_post.assert_called_once()

    # Assert correct token url
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    assert "Authorization" in kwargs["headers"]
    assert "grant_type" in kwargs["data"]

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_get_paypal_access_token_failure(mock_post, mock_env):
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_post.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await PayoutService._get_paypal_access_token()

    assert "PayPal Authentication Failed: 401" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.payout_service.PayoutService._get_paypal_access_token")
@patch("httpx.AsyncClient.post")
async def test_process_paypal_payout_success(mock_post, mock_get_token, mock_env):
    mock_get_token.return_value = "test_access_token"

    # Mock successful payout response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "batch_header": {
            "payout_batch_id": "test_batch_id_123"
        }
    }
    mock_post.return_value = mock_response

    batch_id = await PayoutService._process_paypal_payout("instructor@test.com", Decimal("100.00"))

    assert batch_id == "test_batch_id_123"

    # Assert correct post call
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api-m.sandbox.paypal.com/v1/payments/payouts"
    assert kwargs["headers"]["Authorization"] == "Bearer test_access_token"
    assert kwargs["json"]["items"][0]["receiver"] == "instructor@test.com"
    assert kwargs["json"]["items"][0]["amount"]["value"] == "100.00"

@pytest.mark.asyncio
@patch("app.services.payout_service.PayoutService._get_paypal_access_token")
@patch("httpx.AsyncClient.post")
async def test_process_paypal_payout_failure(mock_post, mock_get_token, mock_env):
    mock_get_token.return_value = "test_access_token"

    # Mock failed payout response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await PayoutService._process_paypal_payout("instructor@test.com", Decimal("100.00"))

    assert "PayPal Payout Failed: 400" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.payout_service.PayoutService._get_paypal_access_token")
@patch("httpx.AsyncClient.post")
async def test_process_paypal_payout_missing_batch_id(mock_post, mock_get_token, mock_env):
    mock_get_token.return_value = "test_access_token"

    # Mock successful response but missing batch id
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"batch_header": {}}
    mock_post.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await PayoutService._process_paypal_payout("instructor@test.com", Decimal("100.00"))

    assert "PayPal API did not return a payout_batch_id" in str(exc_info.value)
