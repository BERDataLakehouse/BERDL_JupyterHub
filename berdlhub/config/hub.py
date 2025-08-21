"""Core JupyterHub configuration."""

import os


def configure_hub(c):
    """Configure core JupyterHub settings."""

    # Network settings
    c.JupyterHub.ip = "0.0.0.0"

    # Security
    c.JupyterHub.cookie_secret = bytes.fromhex(
        os.environ["JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS"]
    )

    # Templates
    c.JupyterHub.template_paths = [os.environ["JUPYTERHUB_TEMPLATES_DIR"]]
    c.JupyterHub.template_vars = {
        "kbase_origin": os.environ["KBASE_ORIGIN"],
    }
