"""User-selectable server profiles."""

import os


def configure_profiles(c):
    """Configure server profile options."""

    berdl_image = os.environ["BERDL_NOTEBOOK_IMAGE_TAG"]

    c.KubeSpawner.profile_list = [
        {
            "display_name": ("Medium"),
            "description": "Balanced Spark cluster for medium data processing workloads",
            "slug": "medium",
            "default": True,
            "kubespawner_override": {
                "mem_limit": "24G",
                "mem_guarantee": "6G",
                "cpu_guarantee": 1,
                "image": berdl_image,
            },
        },
        {
            "display_name": ("Large"),
            "description": "High-performance Spark cluster for large datasets and heavy computation",
            "slug": "large",
            "kubespawner_override": {
                "mem_limit": "24G",
                "mem_guarantee": "6G",
                "cpu_guarantee": 1,
                "image": berdl_image,
            },
        },
    ]
