"""Core JupyterHub configuration."""

import os


def configure_hub(c):
    """Configure core JupyterHub settings."""

    # Network settings
    c.JupyterHub.ip = "0.0.0.0"

    # Security
    c.JupyterHub.cookie_secret = bytes.fromhex(os.environ["JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS"])

    # Templates
    c.JupyterHub.template_paths = [os.environ["JUPYTERHUB_TEMPLATES_DIR"]]
    c.JupyterHub.template_vars = {
        "kbase_origin": os.environ["KBASE_ORIGIN"],
    }

    # Branding - KBase logo (light version, CSS handles dark mode)
    # Static assets are at berdlhub/static/ (sibling to auth/)
    templates_dir = os.environ["JUPYTERHUB_TEMPLATES_DIR"]
    berdl_dir = os.path.dirname(os.path.dirname(templates_dir))
    static_dir = os.path.join(berdl_dir, "static")
    logo_path = os.path.join(static_dir, "kbase-logo-new.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(static_dir, "kbase-logo.png")
    if os.path.exists(logo_path):
        c.JupyterHub.logo_file = logo_path
