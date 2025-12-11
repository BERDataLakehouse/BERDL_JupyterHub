"""Environment variable configuration for spawned pods."""

import os

from .spark_connect_service import sanitize_k8s_name


def get_spark_connect_url(spawner):
    """
    Generate the Spark Connect URL for the user's notebook.

    This callable is used by KubeSpawner to dynamically generate the URL
    based on the sanitized username (matching the Service name).

    Args:
        spawner: KubeSpawner instance

    Returns:
        Spark Connect URL string (sc://jupyter-{sanitized-username}.{namespace}:15002)
    """
    sanitized_username = sanitize_k8s_name(spawner.user.name)
    namespace = spawner.namespace
    return f"sc://jupyter-{sanitized_username}.{namespace}:15002"


def configure_environment(c):
    """Configure environment variables for notebook pods."""

    # BERDL-specific environment variables
    c.KubeSpawner.environment = {
        # KBase integration
        "KBASE_ORIGIN": os.environ["KBASE_ORIGIN"],
        # Spark configuration
        "SPARK_JOB_LOG_DIR_CATEGORY": "{username}",
        "CDM_TASK_SERVICE_URL": os.environ["CDM_TASK_SERVICE_URL"],
        "SPARK_CLUSTER_MANAGER_API_URL": os.environ["SPARK_CLUSTER_MANAGER_API_URL"],
        # Hive metastore
        "BERDL_HIVE_METASTORE_URI": os.environ["BERDL_HIVE_METASTORE_URI"],
        # Python settings
        "PIP_USER": "1",  # Force user installs with pip
        "GOVERNANCE_API_URL": os.environ["GOVERNANCE_API_URL"],
        "MINIO_ENDPOINT_URL": os.environ["MINIO_ENDPOINT_URL"],
        "MINIO_SECURE": os.environ.get("MINIO_SECURE_FLAG", "True"),
        "DATALAKE_MCP_SERVER_URL": os.environ["DATALAKE_MCP_SERVER_URL"],
        "BERDL_REDIS_HOST": os.environ["BERDL_REDIS_HOST"],
        "BERDL_REDIS_PORT": os.environ["BERDL_REDIS_PORT"],
        # Spark Connect URL (uses callable to generate from sanitized username)
        # This must match the Service name created in spark_connect_service.py
        "SPARK_CONNECT_URL": get_spark_connect_url,
        "TENANT_ACCESS_SERVICE_URL": os.environ["TENANT_ACCESS_SERVICE_URL"],
    }

    # Jupyter Docker Stacks configuration
    # https://jupyter-docker-stacks.readthedocs.io/en/latest/using/common.html
    # IMPORTANT: Use {unescaped_username} because c.KubeSpawner.environment goes through
    # _expand_user_properties(), not template_namespace()
    c.KubeSpawner.environment.update({"NB_USER": "{unescaped_username}", "CHOWN_HOME": "yes", "GEN_CERT": "yes"})
