"""Environment variable configuration for spawned pods."""

import os


def configure_environment(c):
    """Configure environment variables for notebook pods."""

    # BERDL-specific environment variables
    c.KubeSpawner.environment = {
        # KBase integration
        "KBASE_ORIGIN": os.environ["KBASE_ORIGIN"],
        # Spark configuration
        "SPARK_JOB_LOG_DIR_CATEGORY": "{unescaped_username}",
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
    }

    # Jupyter Docker Stacks configuration
    # https://jupyter-docker-stacks.readthedocs.io/en/latest/using/common.html
    c.KubeSpawner.environment.update({"NB_USER": "{unescaped_username}", "CHOWN_HOME": "yes", "GEN_CERT": "yes"})
