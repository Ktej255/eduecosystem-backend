"""
Sentry configuration for error tracking and performance monitoring.
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry error tracking and performance monitoring.

    Only enabled in production or if SENTRY_DSN is explicitly configured.
    """
    sentry_dsn = getattr(settings, "SENTRY_DSN", None)

    if not sentry_dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return

    environment = settings.ENVIRONMENT

    # Don't initialize in tests
    if environment == "test" or environment == "testing":
        return

    try:
        # Build integrations list, only including those whose dependencies are installed
        integrations = [
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ]

        # Add optional integrations only if their dependencies are available
        try:
            from sentry_sdk.integrations.redis import RedisIntegration

            integrations.append(RedisIntegration())
        except ImportError:
            logger.debug("Redis integration not available - skipping")

        try:
            from sentry_sdk.integrations.celery import CeleryIntegration

            # Only add if Celery is actually installed
            import celery  # noqa: F401

            integrations.append(CeleryIntegration())
            logger.debug("Celery integration added")
        except ImportError:
            logger.debug("Celery not installed - skipping Celery integration")

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            # Integrations
            integrations=integrations,
            # Performance Monitoring
            traces_sample_rate=0.1
            if environment == "production"
            else 1.0,  # 10% in prod, 100% in dev
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            # Error Sampling
            sample_rate=1.0,  # Capture all errors
            # Release tracking
            release=getattr(settings, "APP_VERSION", "unknown"),
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            max_breadcrumbs=50,
            debug=environment == "development",
            # Before send hook for filtering
            before_send=before_send_hook,
        )

        logger.info(f"Sentry initialized for environment: {environment}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_hook(event, hint):
    """
    Filter and modify events before sending to Sentry.

    This allows us to:
    - Filter out certain errors
    - Scrub sensitive data
    - Add custom context
    """
    # Filter out health check errors
    if "request" in event:
        url = event["request"].get("url", "")
        if "/health" in url or "/metrics" in url:
            return None

    # Filter out known/expected errors
    if "exception" in event:
        exceptions = event["exception"].get("values", [])
        for exc in exceptions:
            exc_type = exc.get("type", "")

            # Don't send validation errors to Sentry
            if "ValidationError" in exc_type:
                return None

            # Don't send 404 errors
            if "NotFoundError" in exc_type or "HTTPException" in exc_type:
                exc_value = exc.get("value", "")
                if "404" in exc_value:
                    return None

    return event


def capture_exception(error: Exception, context: dict = None):
    """
    Manually capture an exception with optional context.

    Args:
        error: The exception to capture
        context: Additional context to attach to the error
    """
    if context:
        sentry_sdk.set_context("custom", context)

    sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Capture a message (not an exception) to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context
    """
    if context:
        sentry_sdk.set_context("custom", context)

    sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: int, email: str = None, username: str = None):
    """
    Set user context for error tracking.

    This helps identify which users are experiencing errors.
    """
    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
            "username": username,
        }
    )


def add_breadcrumb(
    message: str, category: str = "default", level: str = "info", data: dict = None
):
    """
    Add a breadcrumb for debugging context.

    Breadcrumbs are a trail of events that led to an error.
    """
    sentry_sdk.add_breadcrumb(
        message=message, category=category, level=level, data=data or {}
    )
