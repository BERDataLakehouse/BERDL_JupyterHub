"""User-selectable server profiles."""

import os


def configure_profiles(c):
    """Configure server profile options."""

    berdl_image = os.environ["BERDL_NOTEBOOK_IMAGE_TAG"]

    c.KubeSpawner.profile_list = [
        {
            "display_name": "Small Server (2G RAM, 1 CPU)",
            "slug": "small",  # Add explicit slug
            "description": "Suitable for light analysis and development",
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
            "display_name": "Medium Server (8G RAM, 2 CPU)",
            "slug": "medium",  # Add explicit slug
            "description": "For Spark jobs and medium data processing",
            "kubespawner_override": {
                "mem_limit": "8G",
                "mem_guarantee": "4G",
                "cpu_limit": 2,
                "cpu_guarantee": 1,
                "image": berdl_image,
            },
        },
        {
            "display_name": "Large Server (32G RAM, 4 CPU)",
            "slug": "large",  # Add explicit slug
            "description": "For heavy computation and large datasets",
            "kubespawner_override": {
                "mem_limit": "32G",
                "mem_guarantee": "16G",
                "cpu_limit": 4,
                "cpu_guarantee": 2,
                "image": berdl_image,
            },
        },
    ]
