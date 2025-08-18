"""Base spawner configuration."""

import os


def configure_spawner(c):
    """Configure KubeSpawner base settings."""

    c.JupyterHub.spawner_class = "kubespawner.KubeSpawner"

    # Image settings
    c.KubeSpawner.image_pull_policy = "Always"

    # Pod metadata
    c.KubeSpawner.extra_labels = {"app": "berdl-notebook"}
    c.KubeSpawner.extra_pod_config = {
        "enableServiceLinks": False,
    }

    # Networking
    c.KubeSpawner.hub_connect_url = "http://jupyterhub:8000"
    c.KubeSpawner.port = 8888

    # Timeouts
    c.KubeSpawner.start_timeout = 300  # 5 minutes
    c.KubeSpawner.http_timeout = 120  # 2 minutes
    c.KubeSpawner.delete_stopped_pods = True

    # Notebook settings
    c.KubeSpawner.notebook_dir = "/home/{username}"
    c.KubeSpawner.cmd = ["start-notebook.sh"]
    c.KubeSpawner.working_dir = "/home/{username}"
    c.KubeSpawner.notebook_dir = "/home/{username}"
    c.KubeSpawner.args = [
        "--ServerApp.default_url=/lab",
    ]

    # Node selection (if specified)
    node_hostname = os.environ.get("NODE_SELECTOR_HOSTNAME")
    if node_hostname:
        c.KubeSpawner.node_selector = {"kubernetes.io/hostname": node_hostname}
