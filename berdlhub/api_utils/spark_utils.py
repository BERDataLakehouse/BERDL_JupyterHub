import logging
import os
from dataclasses import dataclass
from typing import Optional

from spark_manager_client import AuthenticatedClient
from spark_manager_client.api.clusters import (
    create_cluster_clusters_post,
    delete_cluster_clusters_delete,
)
from spark_manager_client.models import (
    ClusterDeleteResponse,
    SparkClusterConfig,
    SparkClusterCreateResponse,
)
from spark_manager_client.types import Response


@dataclass
class ClusterDefaults:
    """Container for default cluster configuration values."""

    worker_count: int = 2
    worker_cores: int = 1
    worker_memory: str = "10GiB"
    master_cores: int = 1
    master_memory: str = "2GiB"

    # Profile configurations
    PROFILES = {
        "medium": {
            "worker_count": 4,
            "worker_cores": 1,
            "worker_memory": "8GiB",
            "master_cores": 1,
            "master_memory": "8GiB",
        },
        "large": {
            "worker_count": 4,
            "worker_cores": 1,
            "worker_memory": "32GiB",
            "master_cores": 1,
            "master_memory": "16GiB",
        },
    }

    @classmethod
    def from_profile(cls, profile_slug: str) -> "ClusterDefaults":
        """Load defaults from a predefined profile."""
        if profile_slug not in cls.PROFILES:
            profile_slug = "large"  # fallback to default

        profile_config = cls.PROFILES[profile_slug]
        return cls(**profile_config)


class SparkClusterError(Exception):
    """Base exception for Spark cluster operations."""

    pass


class SparkClusterManager:
    """
    A unified async class to manage Spark clusters for users.

    This class handles cluster lifecycle operations including creation and deletion,
    with integration support for JupyterHub spawners.
    """

    def __init__(self, kbase_auth_token: str, api_url: Optional[str] = None):
        """
        Initialize the AsyncSparkClusterManager with authentication.

        Args:
            kbase_auth_token: KBase authentication token (required)
            api_url: Optional API URL, defaults to SPARK_CLUSTER_MANAGER_API_URL env var

        Raises:
            KeyError: If the SPARK_CLUSTER_MANAGER_API_URL is not set and an api_url is not provided
        """
        self.kbase_auth_token = kbase_auth_token
        self.api_url = api_url or os.environ["SPARK_CLUSTER_MANAGER_API_URL"]
        self.logger = logging.getLogger(__name__)
        self.client = AuthenticatedClient(base_url=self.api_url, token=kbase_auth_token)

    def _get_profile_slug_from_spawner(self, spawner) -> str:
        """Get the profile slug from spawner. ClusterDefaults.from_profile will handle fallback."""
        # Get the profile slug from user_options or use 'large' as default
        if spawner.user_options and "profile" in spawner.user_options:
            profile_slug = spawner.user_options["profile"]
            self.logger.info(f"Using profile from user options: {profile_slug}")
            return profile_slug

        self.logger.info("No profile specified in user options, will use default")
        return "large"

    async def _raise_api_error(self, response: Response, operation: str):
        """
        Process API error response and raise appropriate exception.

        Args:
            response: API response object
            operation: Description of the operation that failed

        Raises:
            SparkClusterError: With API error details
        """
        error_message = f"{operation} failed (HTTP {response.status_code})"

        if hasattr(response, "content") and response.content:
            error_message += f": {response.content}"

        self.logger.error(error_message)
        raise SparkClusterError(error_message)

    async def create_cluster(
        self,
        worker_count: int,
        worker_cores: int,
        worker_memory: str,
        master_cores: int,
        master_memory: str,
    ) -> SparkClusterCreateResponse:
        """
        Create a new Spark cluster with the given configuration.

        Args:
            worker_count: Number of worker nodes (required)
            worker_cores: CPU cores per worker (required)
            worker_memory: Memory per worker (required)
            master_cores: CPU cores for master (required)
            master_memory: Memory for master (required)

        Returns:
            SparkClusterCreateResponse: Cluster creation response with master URL

        Raises:
            SparkClusterError: If cluster creation fails
        """
        config = SparkClusterConfig(
            worker_count=worker_count,
            worker_cores=worker_cores,
            worker_memory=worker_memory,
            master_cores=master_cores,
            master_memory=master_memory,
        )

        async with self.client as client:
            response: Response[SparkClusterCreateResponse] = await create_cluster_clusters_post.asyncio_detailed(
                client=client, body=config
            )

        if response.status_code == 201 and response.parsed:
            self.logger.info("Spark cluster created successfully")
            self.logger.info(f"Master URL: {response.parsed.master_url}")
            return response.parsed

        await self._raise_api_error(response, "Cluster creation")

    async def stop_spark_cluster(self, spawner) -> Optional[ClusterDeleteResponse]:
        """
        Stop/delete the Spark cluster for the authenticated user.

        This method combines the functionality of delete_cluster and stop_spark_cluster.
        It can be used both programmatically and with JupyterHub spawners.

        Args:
            spawner: JupyterHub spawner instance for integration.

        Returns:
            ClusterDeleteResponse: Deletion response if available

        Raises:
            SparkClusterError: If cluster deletion fails (only when spawner is None)
        """
        # Determine context and logging

        username = spawner.user.name

        try:
            self.logger.info(f"Deleting Spark cluster for user {username}")

            async with self.client as client:
                response: Response[ClusterDeleteResponse] = await delete_cluster_clusters_delete.asyncio_detailed(
                    client=client
                )

            if response.status_code in (200, 204):
                self.logger.info(f"Spark cluster deleted successfully for {username}")
                return response.parsed

            # If not successful, handle error
            error_message = f"Cluster deletion failed (HTTP {response.status_code})"
            if hasattr(response, "content") and response.content:
                error_message += f": {response.content}"

            self.logger.error(f"Error deleting Spark cluster for user {username}: {error_message}")

        except Exception as e:
            self.logger.error(f"Error deleting Spark cluster for user {username}: {str(e)}")

    async def start_spark_cluster(self, spawner) -> str:
        """
        Create a Spark cluster for the user (async method for spawner integration).

        Automatically determines cluster configuration based on the selected JupyterHub profile.

        Args:
            spawner: JupyterHub spawner instance

        Returns:
            str: The master URL of the created cluster

        Raises:
            SparkClusterError: If cluster creation fails or master URL not found
        """
        username = spawner.user.name
        try:
            # Get the profile slug from the spawner
            profile_slug = self._get_profile_slug_from_spawner(spawner)
            self.logger.info(f"Creating Spark cluster for user {username} with profile '{profile_slug}'")

            # Get cluster configuration from the profile
            cluster_config = ClusterDefaults.from_profile(profile_slug)

            # Create cluster with profile-specific configuration
            response = await self.create_cluster(
                worker_count=cluster_config.worker_count,
                worker_cores=cluster_config.worker_cores,
                worker_memory=cluster_config.worker_memory,
                master_cores=cluster_config.master_cores,
                master_memory=cluster_config.master_memory,
            )

            master_url = getattr(response, "master_url", None)
            if not master_url:
                raise SparkClusterError(f"Master URL not found in response: {response}")

            self.logger.info(f"Spark cluster created with master URL: {master_url}")

            # Set cluster configuration as environment variables for the notebook
            spawner.environment["SPARK_MASTER_URL"] = master_url
            spawner.environment["SPARK_WORKER_COUNT"] = str(cluster_config.worker_count)
            spawner.environment["SPARK_WORKER_CORES"] = str(cluster_config.worker_cores)
            spawner.environment["SPARK_WORKER_MEMORY"] = cluster_config.worker_memory
            spawner.environment["SPARK_MASTER_CORES"] = str(cluster_config.master_cores)
            spawner.environment["SPARK_MASTER_MEMORY"] = cluster_config.master_memory

            self.logger.info(
                f"Set cluster environment variables: "
                f"workers={cluster_config.worker_count}x{cluster_config.worker_cores}cores/"
                f"{cluster_config.worker_memory}, "
                f"master={cluster_config.master_cores}cores/{cluster_config.master_memory}"
            )

            return master_url

        except Exception as e:
            self.logger.error(f"Error creating Spark cluster for user {username}: {str(e)}")
            raise
