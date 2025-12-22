
import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Starting import debug...")
try:
    from app.db.base import Base
    logger.info("Successfully imported app.db.base.Base")
    from app.models.upsc import UPSCPlan
    logger.info("Successfully imported app.models.upsc.UPSCPlan")
except Exception as e:
    logger.error(f"Import failed: {e}")
    raise
logger.info("Done.")
