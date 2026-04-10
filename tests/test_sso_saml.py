import sys
import unittest.mock as mock
import pytest

def test_process_saml_response_import_error():
    """
    Test that process_saml_response raises an Exception when
    onelogin.saml2.auth cannot be imported.
    """
    # Mock SAMLService and SSOConfig without importing them directly
    # to avoid failing if the environment lacks dependencies.
    # However, in a real test run, we would just import it.
    from app.services.sso_service import SAMLService

    # Simulate missing dependency
    with mock.patch.dict(sys.modules, {'onelogin.saml2.auth': None}):
        with pytest.raises(Exception, match="SAML support not available"):
            SAMLService.process_saml_response("fake_response", mock.MagicMock())

def test_build_auth_request_import_error():
    """
    Test that build_auth_request raises an Exception when
    onelogin.saml2.auth cannot be imported.
    """
    from app.services.sso_service import SAMLService

    # Simulate missing dependency (it also requires onelogin.saml2.utils)
    with mock.patch.dict(sys.modules, {'onelogin.saml2.auth': None, 'onelogin.saml2.utils': None}):
        with pytest.raises(Exception, match="SAML support not available"):
            SAMLService.build_auth_request(mock.MagicMock(), "relay_state")
