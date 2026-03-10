"""Storage configuration for user pods.

Home directories are S3 FUSE-mounted via s3fs inside the container (entrypoint.sh).
/dev/fuse is required for s3fs to create FUSE mounts.
"""

import logging

logger = logging.getLogger(__name__)


def configure_storage(c):
    """Configure S3 FUSE-backed home storage."""

    c.KubeSpawner.volumes = [
        # /dev/fuse device needed for s3fs FUSE mounts
        {"name": "dev-fuse", "hostPath": {"path": "/dev/fuse"}},
    ]

    c.KubeSpawner.volume_mounts = [
        {"name": "dev-fuse", "mountPath": "/dev/fuse"},
    ]

    # SYS_ADMIN capability required for s3fs FUSE mounts inside the container.
    # This is the minimum privilege needed — avoids full privileged mode.
    c.KubeSpawner.extra_container_config = {
        "securityContext": {
            "capabilities": {"add": ["SYS_ADMIN"]},
        }
    }
