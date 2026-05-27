import sys
from unittest.mock import MagicMock

sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.testclient'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['celery'] = MagicMock()

import app.services.sso_service
import app.services.saml_service
import app.core.config
print("Syntax OK")
