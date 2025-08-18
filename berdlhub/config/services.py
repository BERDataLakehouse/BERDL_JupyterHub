"""JupyterHub services configuration."""

import os


def configure_services(c):
    """Configure JupyterHub services like idle-culler."""

    services = []

    # Idle culler service
    if os.environ.get("ENABLE_IDLE_CULLER", "true").lower() == "true":
        timeout = os.environ.get("JUPYTERHUB_IDLE_TIMEOUT_SECONDS", "3600")
        services.append(
            {
                "name": "idle-culler",
                "admin": True,
                "command": [
                    "python3",
                    "-m",
                    "jupyterhub_idle_culler",
                    f"--timeout={timeout}",
                    "--cull-every=60",  # Check every 10 minutes
                ],
            }
        )

    # Could add other services here
    # - Announcement service
    # - Usage tracking service
    # - Backup service

    c.JupyterHub.services = services
