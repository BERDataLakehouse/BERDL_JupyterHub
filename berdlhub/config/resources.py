"""Resource management configuration."""

import os


def configure_resources(c):
    """Configure default resource limits and guarantees."""
    # TODO WE MIGHT BE ABLE TO DELETE THIS DUE TO OVERRIDES

    # Memory settings
    mem_limit_gb = os.environ.get("JUPYTERHUB_MEM_LIMIT_GB", "4")
    mem_guarantee_gb = os.environ.get("JUPYTERHUB_MEM_GUARANTEE_GB", "1")
    c.KubeSpawner.mem_limit = f"{mem_limit_gb}G"
    c.KubeSpawner.mem_guarantee = f"{mem_guarantee_gb}G"

    # CPU settings
    cpu_limit = os.environ.get("JUPYTERHUB_CPU_LIMIT", "2.0")
    cpu_guarantee = os.environ.get("JUPYTERHUB_CPU_GUARANTEE", "0.5")
    c.KubeSpawner.cpu_limit = float(cpu_limit)
    c.KubeSpawner.cpu_guarantee = float(cpu_guarantee)
