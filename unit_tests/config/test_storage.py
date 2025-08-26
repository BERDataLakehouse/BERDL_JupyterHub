"""Tests for storage configuration."""

import os
from unittest.mock import Mock, patch
import pytest

from berdlhub.config.storage import configure_hostpath_storage


class TestStorageConfiguration:
    """Test cases for storage configuration functionality."""

    def test_configure_hostpath_storage_with_env_var(self):
        """Test that storage configuration uses HUB_STORAGE_BASE_PATH environment variable."""
        # Mock configuration object
        mock_config = Mock()

        # Test with dev environment path
        with patch.dict(os.environ, {"HUB_STORAGE_BASE_PATH": "/mnt/state/dev/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify volumes are configured correctly
            expected_volumes = [
                {
                    "name": "user-home",
                    "hostPath": {
                        "path": "/mnt/state/dev/hub/{username}",
                        "type": "DirectoryOrCreate",
                    },
                },
                {
                    "name": "user-global",
                    "hostPath": {
                        "path": "/mnt/state/dev/hub/global_share",
                        "type": "DirectoryOrCreate",
                    },
                },
            ]

            assert mock_config.KubeSpawner.volumes == expected_volumes

            # Verify volume mounts are configured correctly
            expected_volume_mounts = [
                {"name": "user-home", "mountPath": "/home/{username}"},
                {"name": "user-global", "mountPath": "/global_share"},
            ]

            assert mock_config.KubeSpawner.volume_mounts == expected_volume_mounts

    def test_configure_hostpath_storage_with_prod_env(self):
        """Test that storage configuration works with production environment path."""
        # Mock configuration object
        mock_config = Mock()

        # Test with prod environment path
        with patch.dict(os.environ, {"HUB_STORAGE_BASE_PATH": "/mnt/state/prod/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify the user-home volume uses the prod path
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/mnt/state/prod/hub/{username}"

            # Verify the user-global volume uses the prod path
            user_global_volume = mock_config.KubeSpawner.volumes[1]
            assert user_global_volume["hostPath"]["path"] == "/mnt/state/prod/hub/global_share"

    def test_configure_hostpath_storage_with_staging_env(self):
        """Test that storage configuration works with staging environment path."""
        # Mock configuration object
        mock_config = Mock()

        # Test with staging environment path
        with patch.dict(os.environ, {"HUB_STORAGE_BASE_PATH": "/mnt/state/staging/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify the paths are correctly constructed
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/mnt/state/staging/hub/{username}"

            user_global_volume = mock_config.KubeSpawner.volumes[1]
            assert user_global_volume["hostPath"]["path"] == "/mnt/state/staging/hub/global_share"

    def test_configure_hostpath_storage_missing_env_var(self):
        """Test that storage configuration fails gracefully when environment variable is missing."""
        # Mock configuration object
        mock_config = Mock()

        # Clear the environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError):
                configure_hostpath_storage(mock_config)

    def test_configure_hostpath_storage_custom_path(self):
        """Test that storage configuration works with a custom path."""
        # Mock configuration object
        mock_config = Mock()

        # Test with a completely different custom path
        with patch.dict(os.environ, {"HUB_STORAGE_BASE_PATH": "/custom/storage/path"}):
            configure_hostpath_storage(mock_config)

            # Verify the custom path is used
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/custom/storage/path/{username}"

            user_global_volume = mock_config.KubeSpawner.volumes[1]
            assert user_global_volume["hostPath"]["path"] == "/custom/storage/path/global_share"


if __name__ == "__main__":
    pytest.main([__file__])
