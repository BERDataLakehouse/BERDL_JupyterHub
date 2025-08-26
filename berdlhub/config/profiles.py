"""User-selectable server profiles."""

import os
import logging

logger = logging.getLogger(__name__)


def _get_notebook_image_tag():
    """Get notebook image tag from external source or fallback to environment variable.

    First tries to read from mounted file, then falls back to environment variable.

    Returns:
        str: The notebook image tag to use
    """
    # Try to read from mounted file/secret first
    image_tag_file = os.environ.get("BERDL_NOTEBOOK_IMAGE_TAG_FILE", "/etc/berdl/notebook-image-tag")

    if os.path.exists(image_tag_file):
        try:
            with open(image_tag_file, "r") as f:
                image_tag = f.read().strip()
                if image_tag:
                    logger.info(f"Using notebook image tag from file {image_tag_file}: {image_tag}")
                    return image_tag
        except Exception as e:
            logger.warning(f"Failed to read notebook image tag from {image_tag_file}: {e}")

    # Fallback to environment variable
    if "BERDL_NOTEBOOK_IMAGE_TAG" in os.environ:
        image_tag = os.environ["BERDL_NOTEBOOK_IMAGE_TAG"]
        logger.info(f"Using notebook image tag from environment variable: {image_tag}")
        return image_tag

    raise ValueError("Neither BERDL_NOTEBOOK_IMAGE_TAG_FILE nor BERDL_NOTEBOOK_IMAGE_TAG is available")


def configure_profiles(c):
    """Configure server profile options."""

    berdl_image = _get_notebook_image_tag()

    c.KubeSpawner.profile_list = [
        {
            "display_name": "Small Server (2G RAM, 1 CPU)",
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
