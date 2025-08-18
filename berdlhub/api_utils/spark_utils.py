"""
CDM Spark Cluster Manager API Client Wrapper - Async Version
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional, Any
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
    master_memory: str = "10GiB"

    @classmethod
    def from_environment(cls) -> "ClusterDefaults":
        """Load defaults from environment variables."""
        return cls(
            worker_count=int(os.environ.get("DEFAULT_WORKER_COUNT", 2)),
            worker_cores=int(os.environ.get("DEFAULT_WORKER_CORES", 1)),
            worker_memory=os.environ.get("DEFAULT_WORKER_MEMORY", "10GiB"),
            master_cores=int(os.environ.get("DEFAULT_MASTER_CORES", 1)),
            master_memory=os.environ.get("DEFAULT_MASTER_MEMORY", "10GiB"),
        )


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
            KeyError: If SPARK_CLUSTER_MANAGER_API_URL is not set and api_url not provided
        """
        self.kbase_auth_token = kbase_auth_token
        self.api_url = api_url or os.environ["SPARK_CLUSTER_MANAGER_API_URL"]
        self.defaults = ClusterDefaults.from_environment()
        self.logger = logging.getLogger(__name__)
        self.client = AuthenticatedClient(base_url=self.api_url, token=kbase_auth_token)

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

    def _build_cluster_config(
        self,
        worker_count: Optional[int] = None,
        worker_cores: Optional[int] = None,
        worker_memory: Optional[str] = None,
        master_cores: Optional[int] = None,
        master_memory: Optional[str] = None,
    ) -> SparkClusterConfig:
        """
        Build cluster configuration with provided values or defaults.

        Args:
            worker_count: Number of worker nodes
            worker_cores: CPU cores per worker
            worker_memory: Memory per worker
            master_cores: CPU cores for master
            master_memory: Memory for master

        Returns:
            SparkClusterConfig: Configuration object for cluster creation
        """
        return SparkClusterConfig(
            worker_count=(worker_count if worker_count is not None else self.defaults.worker_count),
            worker_cores=(worker_cores if worker_cores is not None else self.defaults.worker_cores),
            worker_memory=worker_memory or self.defaults.worker_memory,
            master_cores=(master_cores if master_cores is not None else self.defaults.master_cores),
            master_memory=master_memory or self.defaults.master_memory,
        )

    async def create_cluster(
        self,
        worker_count: Optional[int] = None,
        worker_cores: Optional[int] = None,
        worker_memory: Optional[str] = None,
        master_cores: Optional[int] = None,
        master_memory: Optional[str] = None,
    ) -> SparkClusterCreateResponse:
        """
        Create a new Spark cluster with the given configuration.

        Args:
            worker_count: Number of worker nodes (defaults from environment)
            worker_cores: CPU cores per worker (defaults from environment)
            worker_memory: Memory per worker (defaults from environment)
            master_cores: CPU cores for master (defaults from environment)
            master_memory: Memory for master (defaults from environment)

        Returns:
            SparkClusterCreateResponse: Cluster creation response with master URL

        Raises:
            SparkClusterError: If cluster creation fails
        """
        config = self._build_cluster_config(worker_count, worker_cores, worker_memory, master_cores, master_memory)

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
            spawner: Optional JupyterHub spawner instance for integration.
                     If provided, will log using spawner's logger.

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

            if spawner:
                # Log error but don't raise when called from spawner
                self.logger.error(f"Error deleting Spark cluster for user {username}: {error_message}")
            else:
                # Raise error when called directly
                await self._raise_api_error(response, "Cluster deletion")

        except Exception as e:
            if spawner:
                # Log error but don't raise when called from spawner
                self.logger.error(f"Error deleting Spark cluster for user {username}: {str(e)}")
            else:
                # Re-raise when called directly
                raise

    async def start_spark_cluster(self, spawner) -> str:
        """
        Create a Spark cluster for the user (async method for spawner integration).

        Args:
            spawner: JupyterHub spawner instance

        Returns:
            str: The master URL of the created cluster

        Raises:
            SparkClusterError: If cluster creation fails or master URL not found
        """
        username = spawner.user.name
        try:
            self.logger.info(f"Creating Spark cluster for user {username}")
            response = await self.create_cluster()

            master_url = getattr(response, "master_url", None)
            if not master_url:
                raise SparkClusterError(f"Master URL not found in response: {response}")

            self.logger.info(f"Spark cluster created with master URL: {master_url}")
            spawner.environment["SPARK_MASTER_URL"] = master_url
            return master_url

        except Exception as e:
            self.logger.error(f"Error creating Spark cluster for user {username}: {str(e)}")
            raise
