"""Common auditing utilities used across the platform."""

import logging

logger = logging.getLogger(__name__)


def audit_log(message: str, **context):
    """Log an audit event."""
    logger.info("AUDIT: %s | %s", message, context)
