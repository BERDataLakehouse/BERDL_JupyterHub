"""Storage configuration for user pods."""

import logging

logger = logging.getLogger(__name__)


def configure_hostpath_storage(c):
    """Configure hostPath volumes (current implementation)."""
    logger.warning("Using hostPath storage - this limits scalability to a single node!")

    c.KubeSpawner.volumes = [
        {
            "name": "user-home",
            "hostPath": {
                "path": "/mnt/state/hub/{username}",
                "type": "DirectoryOrCreate",
            },
        },
        {
            "name": "user-global",
            "hostPath": {
                "path": "/mnt/state/hub/global_share",
                "type": "DirectoryOrCreate",
            },
        },
    ]

    c.KubeSpawner.volume_mounts = [
        {"name": "user-home", "mountPath": "/home/{username}"},
        {"name": "user-global", "mountPath": "/global_share"},
    ]
