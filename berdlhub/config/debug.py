"""Debug configuration - should be disabled in production."""

import logging
import os

logger = logging.getLogger(__name__)


def configure_debug(c):
    """Configure debug settings based on environment."""

    debug_enabled = os.environ.get("JUPYTERHUB_DEBUG", "true").lower() == "true"

    if debug_enabled:
        c.KubeSpawner.debug = True
        c.JupyterHub.log_level = "DEBUG"
        c.KubeSpawner.events_enabled = True
        c.JupyterHub.log_datefmt = "%Y-%m-%d %H:%M:%S"
    else:
        c.KubeSpawner.debug = False
        c.JupyterHub.log_level = os.environ.get("JUPYTERHUB_LOG_LEVEL", "INFO")
