"""User-selectable server profiles."""

import os


def configure_profiles(c):
    """Configure server profile options."""

    berdl_image = os.environ["BERDL_NOTEBOOK_IMAGE_TAG"]

    c.KubeSpawner.profile_list = [
        {
            "display_name": "Small: Spark 1 Worker (2GB, 1 core) + Master (1GB, 1 core) - Notebook (2GB, 1 core)",
            "description": "Minimal Spark cluster for light analysis and development",
            "slug": "small",
            "default": True,
            "kubespawner_override": {
                "mem_limit": "2G",
                "mem_guarantee": "1G",
                "cpu_limit": 1,
                "cpu_guarantee": 0.5,
                "image": berdl_image,
            },
        },
        {
            "display_name": (
                "Medium: Spark 4 Workers (8GB, 1 core each) + Master (8GB, 1 core) - Notebook (16GB, 2 cores)"
            ),
            "description": "Balanced Spark cluster for medium data processing workloads",
            "slug": "medium",
            "kubespawner_override": {
                "mem_limit": "16G",
                "mem_guarantee": "8G",
                "cpu_limit": 2,
                "cpu_guarantee": 1,
                "image": berdl_image,
            },
        },
        {
            "display_name": (
                "Large: Spark 4 Workers (32GB, 1 core each) + Master (16GB, 1 core) - Notebook (72GB, 4 cores)"
            ),
            "description": "High-performance Spark cluster for large datasets and heavy computation",
            "slug": "large",
            "kubespawner_override": {
                "mem_limit": "72G",
                "mem_guarantee": "36G",
                "cpu_limit": 4,
                "cpu_guarantee": 2,
                "image": berdl_image,
            },
        },
    ]
