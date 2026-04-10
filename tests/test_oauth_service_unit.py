import pytest
from unittest.mock import patch, Mock
import httpx
from jose import jwt

def test_verify_id_token_success():
    from app.services.oauth_service import OAuthService
    config = Mock()
    config.client_id = "test_client"
    config.settings = {"jwks_uri": "https://example.com/jwks", "issuer": "https://example.com"}

    service = OAuthService(config)

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "key_1",
                "use": "sig",
                "n": "dummy_n",
                "e": "dummy_e"
            }
        ]
    }

    mock_claims = {"sub": "123", "iss": "https://example.com", "aud": "test_client"}

    with patch("httpx.Client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_jwks
        mock_get.return_value = mock_resp

        with patch("jose.jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {"kid": "key_1", "alg": "RS256"}

            with patch("jose.jwt.decode") as mock_decode:
                mock_decode.return_value = mock_claims

                success, claims = service.verify_id_token("dummy_token")

                assert success is True
                assert claims == mock_claims
                mock_decode.assert_called_once_with(
                    "dummy_token",
                    {"kty": "RSA", "kid": "key_1", "use": "sig", "n": "dummy_n", "e": "dummy_e"},
                    algorithms=["RS256"],
                    audience="test_client",
                    issuer="https://example.com",
                    options={
                        "verify_signature": True,
                        "verify_aud": True,
                        "verify_exp": True,
                        "verify_iss": True
                    }
                )

def test_verify_id_token_missing_kid():
    from app.services.oauth_service import OAuthService
    config = Mock()
    config.client_id = "test_client"
    config.settings = {"jwks_uri": "https://example.com/jwks"}

    service = OAuthService(config)

    with patch("httpx.Client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"keys": [{"kid": "key_1"}]}
        mock_get.return_value = mock_resp

        with patch("jose.jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {"alg": "RS256"} # missing kid

            success, claims = service.verify_id_token("dummy_token")

            assert success is False
            assert claims is None
