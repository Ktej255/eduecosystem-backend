import sys
from unittest.mock import MagicMock

# Mocking external dependencies before they are imported by app modules
sys.modules["httpx"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["pydantic"] = MagicMock()
sys.modules["pydantic_settings"] = MagicMock()

import pytest
import asyncio
from unittest.mock import patch
from app.services.ai_service import AIService

@pytest.fixture
def ai_service():
    return AIService()

@pytest.fixture
def mock_gemini_service():
    with patch("app.services.ai_service.gemini_service") as mock:
        yield mock

def run_async(coro):
    return asyncio.run(coro)

def test_generate_text_no_system_message(ai_service, mock_gemini_service):
    """Test generating text without a system message."""
    prompt = "Hello AI"
    run_async(ai_service.generate_text(prompt=prompt))

    mock_gemini_service.generate_text.assert_called_once_with(
        prompt=prompt,
        user=None,
        temperature=0.7,
        max_tokens=1000
    )

def test_generate_text_user_propagation(ai_service, mock_gemini_service):
    """Test that the user object is correctly propagated to gemini_service."""
    prompt = "Hello AI"
    mock_user = MagicMock()
    run_async(ai_service.generate_text(prompt=prompt, user=mock_user))

    mock_gemini_service.generate_text.assert_called_once_with(
        prompt=prompt,
        user=mock_user,
        temperature=0.7,
        max_tokens=1000
    )

def test_generate_text_extreme_temperature(ai_service, mock_gemini_service):
    """Test generating text with extreme temperature values."""
    prompt = "Hello AI"

    # Temperature 0.0
    run_async(ai_service.generate_text(prompt=prompt, temperature=0.0))
    mock_gemini_service.generate_text.assert_called_with(
        prompt=prompt,
        user=None,
        temperature=0.0,
        max_tokens=1000
    )

    # Temperature 1.0
    run_async(ai_service.generate_text(prompt=prompt, temperature=1.0))
    mock_gemini_service.generate_text.assert_called_with(
        prompt=prompt,
        user=None,
        temperature=1.0,
        max_tokens=1000
    )

def test_generate_text_extreme_max_tokens(ai_service, mock_gemini_service):
    """Test generating text with extreme max_tokens values."""
    prompt = "Hello AI"

    # Very small max_tokens
    run_async(ai_service.generate_text(prompt=prompt, max_tokens=1))
    mock_gemini_service.generate_text.assert_called_with(
        prompt=prompt,
        user=None,
        temperature=0.7,
        max_tokens=1
    )

    # Very large max_tokens
    run_async(ai_service.generate_text(prompt=prompt, max_tokens=10000))
    mock_gemini_service.generate_text.assert_called_with(
        prompt=prompt,
        user=None,
        temperature=0.7,
        max_tokens=10000
    )

def test_generate_text_empty_prompt(ai_service, mock_gemini_service):
    """Test generating text with an empty prompt."""
    prompt = ""
    system_message = "Be helpful"
    run_async(ai_service.generate_text(prompt=prompt, system_message=system_message))

    mock_gemini_service.generate_text.assert_called_once_with(
        prompt=f"{system_message}\n\n",
        user=None,
        temperature=0.7,
        max_tokens=1000
    )
