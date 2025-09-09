import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from spark_manager_client.models import (
    ClusterDeleteResponse,
    SparkClusterCreateResponse,
)

# Import the classes to test
from berdlhub.api_utils.spark_utils import (
    ClusterDefaults,
    SparkClusterError,
    SparkClusterManager,
)


class TestClusterDefaults:
    """Test cases for ClusterDefaults dataclass."""

    def test_default_values(self):
        """Test default initialization values."""
        defaults = ClusterDefaults()
        assert defaults.worker_count == 2
        assert defaults.worker_cores == 1
        assert defaults.worker_memory == "10GiB"
        assert defaults.master_cores == 1
        assert defaults.master_memory == "2GiB"

    def test_custom_values(self):
        """Test initialization with custom values."""
        defaults = ClusterDefaults(
            worker_count=4,
            worker_cores=2,
            worker_memory="20GiB",
            master_cores=2,
            master_memory="4GiB",
        )
        assert defaults.worker_count == 4
        assert defaults.worker_cores == 2
        assert defaults.worker_memory == "20GiB"
        assert defaults.master_cores == 2
        assert defaults.master_memory == "4GiB"

    @patch.dict(
        os.environ,
        {
            "DEFAULT_WORKER_COUNT": "5",
            "DEFAULT_WORKER_CORES": "3",
            "DEFAULT_WORKER_MEMORY": "15GiB",
            "DEFAULT_MASTER_CORES": "2",
            "DEFAULT_MASTER_MEMORY": "3GiB",
        },
    )
    def test_from_environment_with_env_vars(self):
        """Test loading from environment variables."""
        defaults = ClusterDefaults.from_environment()
        assert defaults.worker_count == 5
        assert defaults.worker_cores == 3
        assert defaults.worker_memory == "15GiB"
        assert defaults.master_cores == 2
        assert defaults.master_memory == "3GiB"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_without_env_vars(self):
        """Test loading from environment without variables set."""
        defaults = ClusterDefaults.from_environment()
        assert defaults.worker_count == 2
        assert defaults.worker_cores == 1
        assert defaults.worker_memory == "10GiB"
        assert defaults.master_cores == 1
        assert defaults.master_memory == "2GiB"


class TestSparkClusterManager:
    """Test cases for SparkClusterManager."""

    @pytest.fixture
    def mock_client(self):
        """Mock authenticated client."""
        with patch("berdlhub.api_utils.spark_utils.AuthenticatedClient") as mock:
            yield mock

    @pytest.fixture
    def manager(self, mock_client):
        """Create SparkClusterManager instance for testing."""
        with patch.dict(os.environ, {"SPARK_CLUSTER_MANAGER_API_URL": "http://test-api"}):
            return SparkClusterManager("test-token")

    def test_init_with_api_url(self, mock_client):
        """Test initialization with explicit API URL."""
        manager = SparkClusterManager("test-token", "http://custom-api")
        assert manager.kbase_auth_token == "test-token"
        assert manager.api_url == "http://custom-api"
        mock_client.assert_called_once_with(base_url="http://custom-api", token="test-token")

    @patch.dict(os.environ, {"SPARK_CLUSTER_MANAGER_API_URL": "http://env-api"})
    def test_init_with_env_api_url(self, mock_client):
        """Test initialization with API URL from environment."""
        manager = SparkClusterManager("test-token")
        assert manager.api_url == "http://env-api"

    def test_init_without_api_url_raises_error(self, mock_client):
        """Test initialization fails without API URL."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError):
                SparkClusterManager("test-token")

    def test_build_cluster_config_defaults(self, manager):
        """Test building cluster config with default values."""
        config = manager._build_cluster_config()
        assert config.worker_count == 2
        assert config.worker_cores == 1
        assert config.worker_memory == "10GiB"
        assert config.master_cores == 1
        assert config.master_memory == "2GiB"

    def test_build_cluster_config_custom_values(self, manager):
        """Test building cluster config with custom values."""
        config = manager._build_cluster_config(
            worker_count=4,
            worker_cores=2,
            worker_memory="20GiB",
            master_cores=2,
            master_memory="4GiB",
        )
        assert config.worker_count == 4
        assert config.worker_cores == 2
        assert config.worker_memory == "20GiB"
        assert config.master_cores == 2
        assert config.master_memory == "4GiB"

    def test_build_cluster_config_partial_values(self, manager):
        """Test building cluster config with some custom values."""
        config = manager._build_cluster_config(worker_count=3, worker_memory="15GiB")
        assert config.worker_count == 3
        assert config.worker_cores == 1  # default
        assert config.worker_memory == "15GiB"
        assert config.master_cores == 1  # default
        assert config.master_memory == "2GiB"  # default

    @pytest.mark.asyncio
    async def test_raise_api_error(self, manager):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = "Bad Request"

        with pytest.raises(SparkClusterError, match="Test operation failed \\(HTTP 400\\): Bad Request"):
            await manager._raise_api_error(mock_response, "Test operation")

    @pytest.mark.asyncio
    async def test_raise_api_error_no_content(self, manager):
        """Test API error handling without content."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = None

        with pytest.raises(SparkClusterError, match="Test operation failed \\(HTTP 500\\)"):
            await manager._raise_api_error(mock_response, "Test operation")

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.create_cluster_clusters_post.asyncio_detailed")
    async def test_create_cluster_success(self, mock_create, manager):
        """Test successful cluster creation."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.parsed = SparkClusterCreateResponse(
            cluster_id="test-cluster-123",
            master_url="spark://test:7077",
            master_ui_url="http://test:8080",
        )
        mock_create.return_value = mock_response

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        result = await manager.create_cluster(worker_count=3)

        assert result.master_url == "spark://test:7077"
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.create_cluster_clusters_post.asyncio_detailed")
    async def test_create_cluster_failure(self, mock_create, manager):
        """Test cluster creation failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = "Invalid config"
        mock_response.parsed = None
        mock_create.return_value = mock_response

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(
            SparkClusterError,
            match="Cluster creation failed \\(HTTP 400\\): Invalid config",
        ):
            await manager.create_cluster()

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.delete_cluster_clusters_delete.asyncio_detailed")
    async def test_stop_spark_cluster_success(self, mock_delete, manager):
        """Test successful cluster deletion."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.parsed = ClusterDeleteResponse(message="Cluster deleted successfully")
        mock_delete.return_value = mock_response

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        result = await manager.stop_spark_cluster(mock_spawner)

        assert result is not None
        mock_delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.delete_cluster_clusters_delete.asyncio_detailed")
    async def test_stop_spark_cluster_204_response(self, mock_delete, manager):
        """Test cluster deletion with 204 response."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.parsed = None
        mock_delete.return_value = mock_response

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        result = await manager.stop_spark_cluster(mock_spawner)

        assert result is None
        mock_delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.delete_cluster_clusters_delete.asyncio_detailed")
    async def test_stop_spark_cluster_failure(self, mock_delete, manager):
        """Test cluster deletion failure - should not raise exception."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"

        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = "Cluster not found"
        mock_delete.return_value = mock_response

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        # Should not raise exception
        result = await manager.stop_spark_cluster(mock_spawner)
        assert result is None

    @pytest.mark.asyncio
    @patch("berdlhub.api_utils.spark_utils.delete_cluster_clusters_delete.asyncio_detailed")
    async def test_stop_spark_cluster_exception(self, mock_delete, manager):
        """Test cluster deletion with exception."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"

        # Mock exception
        mock_delete.side_effect = Exception("Network error")

        # Mock client context manager
        manager.client.__aenter__ = AsyncMock(return_value=manager.client)
        manager.client.__aexit__ = AsyncMock(return_value=None)

        # Should not raise exception, just log error
        result = await manager.stop_spark_cluster(mock_spawner)
        assert result is None

    @pytest.mark.asyncio
    async def test_start_spark_cluster_success(self, manager):
        """Test successful cluster start for spawner."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"
        mock_spawner.environment = {}
        mock_spawner.profile_list = [{"slug": "small", "display_name": "Small"}]
        mock_spawner.user_options = {"profile": "small"}

        # Mock create_cluster method
        mock_response = SparkClusterCreateResponse(
            cluster_id="test-cluster-123",
            master_url="spark://test:7077",
            master_ui_url="http://test:8080",
        )
        manager.create_cluster = AsyncMock(return_value=mock_response)

        result = await manager.start_spark_cluster(mock_spawner)

        assert result == "spark://test:7077"
        assert mock_spawner.environment["SPARK_MASTER_URL"] == "spark://test:7077"
        manager.create_cluster.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_spark_cluster_no_master_url(self, manager):
        """Test cluster start failure when no master URL in response."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"
        mock_spawner.profile_list = [{"slug": "small", "display_name": "Small"}]
        mock_spawner.user_options = {"profile": "small"}

        # Mock create_cluster method with response without master_url
        mock_response = Mock()
        mock_response.master_url = None
        manager.create_cluster = AsyncMock(return_value=mock_response)

        with pytest.raises(SparkClusterError, match="Master URL not found in response"):
            await manager.start_spark_cluster(mock_spawner)

    @pytest.mark.asyncio
    async def test_start_spark_cluster_create_failure(self, manager):
        """Test cluster start failure when create_cluster fails."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"
        mock_spawner.profile_list = [{"slug": "small", "display_name": "Small"}]
        mock_spawner.user_options = {"profile": "small"}

        # Mock create_cluster method to raise exception
        manager.create_cluster = AsyncMock(side_effect=SparkClusterError("Creation failed"))

        with pytest.raises(SparkClusterError, match="Creation failed"):
            await manager.start_spark_cluster(mock_spawner)


class TestSparkClusterError:
    """Test cases for SparkClusterError exception."""

    def test_spark_cluster_error_creation(self):
        """Test SparkClusterError can be created and raised."""
        error = SparkClusterError("Test error message")
        assert str(error) == "Test error message"

        with pytest.raises(SparkClusterError, match="Test error message"):
            raise error


# Integration tests
class TestSparkClusterManagerIntegration:
    """Integration test cases."""

    @pytest.fixture
    def manager_with_env(self):
        """Create manager with environment variables set."""
        env_vars = {
            "SPARK_CLUSTER_MANAGER_API_URL": "http://test-api",
            "DEFAULT_WORKER_COUNT": "3",
            "DEFAULT_WORKER_CORES": "2",
            "DEFAULT_WORKER_MEMORY": "15GiB",
            "DEFAULT_MASTER_CORES": "2",
            "DEFAULT_MASTER_MEMORY": "3GiB",
        }

        with patch.dict(os.environ, env_vars):
            with patch("berdlhub.api_utils.spark_utils.AuthenticatedClient"):
                yield SparkClusterManager("test-token")

    def test_manager_uses_environment_defaults(self, manager_with_env):
        """Test that manager uses environment-based defaults."""
        config = manager_with_env._build_cluster_config()
        assert config.worker_count == 3
        assert config.worker_cores == 2
        assert config.worker_memory == "15GiB"
        assert config.master_cores == 2
        assert config.master_memory == "3GiB"

    @pytest.mark.asyncio
    async def test_full_cluster_lifecycle(self, manager_with_env):
        """Test complete cluster lifecycle (create -> delete)."""
        # Mock spawner
        mock_spawner = Mock()
        mock_spawner.user.name = "testuser"
        mock_spawner.environment = {}
        mock_spawner.profile_list = [{"slug": "small", "display_name": "Small"}]
        mock_spawner.user_options = {"profile": "small"}

        # Mock create_cluster
        create_response = SparkClusterCreateResponse(
            cluster_id="test-cluster-123",
            master_url="spark://test:7077",
            master_ui_url="http://test:8080",
        )
        manager_with_env.create_cluster = AsyncMock(return_value=create_response)

        # Mock stop_spark_cluster
        delete_response = ClusterDeleteResponse(message="Cluster deleted successfully")
        manager_with_env.stop_spark_cluster = AsyncMock(return_value=delete_response)

        # Test create
        master_url = await manager_with_env.start_spark_cluster(mock_spawner)
        assert master_url == "spark://test:7077"
        assert mock_spawner.environment["SPARK_MASTER_URL"] == "spark://test:7077"

        # Test delete
        result = await manager_with_env.stop_spark_cluster(mock_spawner)
        assert result == delete_response


if __name__ == "__main__":
    pytest.main([__file__])
