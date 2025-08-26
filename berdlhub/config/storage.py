"""Storage configuration for user pods."""

import logging
import os

logger = logging.getLogger(__name__)


def configure_hostpath_storage(c):
    """Configure hostPath volumes (current implementation)."""
    logger.warning("Using hostPath storage - this limits scalability to a single node!")

    # Get configurable base path for storage
    storage_base_path = os.environ["HUB_STORAGE_BASE_PATH"]

    c.KubeSpawner.volumes = [
        {
            "name": "user-home",
            "hostPath": {
                "path": f"{storage_base_path}/{{username}}",
                "type": "DirectoryOrCreate",
            },
        },
        {
            "name": "user-global",
            "hostPath": {
                "path": f"{storage_base_path}/global_share",
                "type": "DirectoryOrCreate",
            },
        },
    ]

    c.KubeSpawner.volume_mounts = [
        {"name": "user-home", "mountPath": "/home/{username}"},
        {"name": "user-global", "mountPath": "/global_share"},
    ]
