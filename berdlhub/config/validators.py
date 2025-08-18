"""Validate required environment variables."""

import os
import sys
import logging

logger = logging.getLogger(__name__)


def validate_environment():
    """Validate that all required environment variables are set."""

    required_vars = {
        # Core JupyterHub
        "JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS": "64 character hex string for cookies",
        "JUPYTERHUB_TEMPLATES_DIR": "Path to JupyterHub templates",
        # KBase integration
        "KBASE_ORIGIN": "KBase origin URL",
        "KBASE_AUTH_URL": "KBase authentication service URL",
        # Services
        "CDM_TASK_SERVICE_URL": "CDM task service endpoint",
        "GOVERNANCE_API_URL": "Governance API endpoint",
        "MINIO_ENDPOINT_URL": "MinIO endpoint URL for the governance service to inject into the users env",
        "SPARK_CLUSTER_MANAGER_API_URL": "Spark cluster manager API",
        "BERDL_HIVE_METASTORE_URI": "Hive metastore URI",
        "BERDL_NOTEBOOK_IMAGE_TAG": "Docker image tag for the notebook server",
    }

    optional_vars = {
        "NODE_SELECTOR_HOSTNAME": "Kubernetes node hostname",
        "JUPYTERHUB_DEBUG": "Enable debug mode",
        "JUPYTERHUB_LOG_LEVEL": "Set JupyterHub log level. Default is INFO",
        "DEFAULT_MASTER_CORES": "Default master cores for Spark clusters",
        "DEFAULT_MASTER_MEMORY": "Default master memory for Spark clusters",
        "DEFAULT_WORKER_COUNT": "Default number of worker nodes for Spark clusters",
        "DEFAULT_WORKER_CORES": "Default worker cores for Spark clusters",
        "DEFAULT_WORKER_MEMORY": "Default worker memory for Spark clusters",
        "MINIO_SECURE_FLAG": "Flag indicating if MinIO uses HTTPS to inject into the users env. Defaults to True",
        "ENABLE_IDLE_CULLER": "Enable idle culler for JupyterHub. Defaults to True",
        "JUPYTERHUB_IDLE_TIMEOUT_SECONDS": "Idle Culler timeout seconds. Defaults to 3600 seconds (1 hour)",
        "JUPYTERHUB_MEM_LIMIT_GB": "Memory limit in GB for JupyterHub users. Defaults to 4GB",
        "JUPYTERHUB_MEM_GUARANTEE_GB": "Memory guarantee in GB for JupyterHub users. Defaults to 2GB",
        "JUPYTERHUB_CPU_LIMIT": "CPU limit for JupyterHub users. Defaults to 2 cores",
    }

    # Check required variables
    missing = []
    for var, description in required_vars.items():
        if var not in os.environ:
            missing.append(f"  - {var}: {description}")

    if missing:
        logging.error("ERROR: Missing required environment variables:")
        logging.error("\n".join(missing))
        sys.exit(1)

    logger.info("Environment validation successful!")
    logger.info("\nOptional variables status:")
    for var, description in optional_vars.items():
        status = "✓ Set" if var in os.environ else "✗ Not set"
        logger.info(f"  {status}: {var} ({description})")
