"""Bootstrap helpers for the application runtime.

The project currently does not use a persistent database/bootstrap layer at
startup, so the function below is intentionally a no-op. Keeping this module
present avoids import errors from the app entry point while allowing future
startup initialization to be added in one place.
"""

import logging

logger = logging.getLogger(__name__)


def bootstrap_application_data() -> None:
    """Prepare application data before the bot starts polling."""
    logger.info("Application bootstrap: nothing to initialize at startup.")
