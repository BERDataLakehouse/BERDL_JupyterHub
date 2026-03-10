"""Tests for storage configuration."""

from unittest.mock import Mock

import pytest

from berdlhub.config.storage import configure_storage


class TestStorageConfiguration:
    """Test cases for S3 FUSE-backed storage configuration."""

    def test_configure_storage_volumes(self):
        """Test that storage configuration creates dev-fuse volume."""
        mock_config = Mock()

        configure_storage(mock_config)

        expected_volumes = [
            {"name": "dev-fuse", "hostPath": {"path": "/dev/fuse"}},
        ]

        assert mock_config.KubeSpawner.volumes == expected_volumes

    def test_configure_storage_volume_mounts(self):
        """Test that volume mounts point to /dev/fuse."""
        mock_config = Mock()

        configure_storage(mock_config)

        expected_volume_mounts = [
            {"name": "dev-fuse", "mountPath": "/dev/fuse"},
        ]

        assert mock_config.KubeSpawner.volume_mounts == expected_volume_mounts

    def test_configure_storage_security_context(self):
        """Test that SYS_ADMIN capability is set for FUSE mounts."""
        mock_config = Mock()

        configure_storage(mock_config)

        expected_extra_config = {
            "securityContext": {
                "capabilities": {"add": ["SYS_ADMIN"]},
            }
        }

        assert mock_config.KubeSpawner.extra_container_config == expected_extra_config

    def test_configure_storage_no_env_vars_needed(self):
        """Test that storage configuration does not require environment variables."""
        mock_config = Mock()

        # Should not raise any exception — no env vars needed
        configure_storage(mock_config)


if __name__ == "__main__":
    pytest.main([__file__])
