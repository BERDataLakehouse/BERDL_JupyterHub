"""User-selectable server profiles."""

import os


def configure_profiles(c):
    """Configure server profile options."""

    berdl_image = os.environ["BERDL_NOTEBOOK_IMAGE_TAG"]

    c.KubeSpawner.profile_list = [
        {
            "display_name": "Small: 1 Worker (2GB, 1 core) + Master (1GB, 1 core)",
            "description": "Minimal Spark cluster for light analysis and development",
            "default": True,
            "kubespawner_override": {
                "mem_limit": "2G",
                "mem_guarantee": "1G",
                "cpu_limit": 1,
                "cpu_guarantee": 0.5,
                "image": berdl_image,
                "environment": {
                    "DEFAULT_WORKER_COUNT": "1",
                    "DEFAULT_WORKER_CORES": "1",
                    "DEFAULT_WORKER_MEMORY": "2GiB",
                    "DEFAULT_MASTER_CORES": "1",
                    "DEFAULT_MASTER_MEMORY": "1GiB"
                }
            },
        },
        {
            "display_name": "Medium: 4 Workers (8GB, 1 core each) + Master (8GB, 1 core)",
            "description": "Balanced Spark cluster for medium data processing workloads",
            "kubespawner_override": {
                "mem_limit": "8G",
                "mem_guarantee": "4G",
                "cpu_limit": 2,
                "cpu_guarantee": 1,
                "image": berdl_image,
                "environment": {
                    "DEFAULT_WORKER_COUNT": "4",
                    "DEFAULT_WORKER_CORES": "1",
                    "DEFAULT_WORKER_MEMORY": "8GiB",
                    "DEFAULT_MASTER_CORES": "1",
                    "DEFAULT_MASTER_MEMORY": "8GiB"
                }
            },
        },
        {
            "display_name": "Large: 4 Workers (32GB, 1 core each) + Master (16GB, 1 core)",
            "description": "High-performance Spark cluster for large datasets and heavy computation",
            "kubespawner_override": {
                "mem_limit": "32G",
                "mem_guarantee": "16G",
                "cpu_limit": 4,
                "cpu_guarantee": 2,
                "image": berdl_image,
                "environment": {
                    "DEFAULT_WORKER_COUNT": "4",
                    "DEFAULT_WORKER_CORES": "1",
                    "DEFAULT_WORKER_MEMORY": "32GiB",
                    "DEFAULT_MASTER_CORES": "1",
                    "DEFAULT_MASTER_MEMORY": "16GiB"
                }
            },
        },
    ]
