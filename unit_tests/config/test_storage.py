"""Tests for storage configuration."""

import os
from unittest.mock import Mock, patch
import pytest

from berdlhub.config.storage import configure_hostpath_storage


class TestStorageConfiguration:
    """Test cases for storage configuration functionality."""

    def test_configure_hostpath_storage_with_env_var(self):
        """Test that storage configuration uses BERDL_NOTEBOOK_HOMES_DIR environment variable."""
        # Mock configuration object
        mock_config = Mock()

        # Test with dev environment path
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_HOMES_DIR": "/mnt/state/dev/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify volumes are configured correctly
            expected_volumes = [
                {
                    "name": "user-home",
                    "hostPath": {
                        "path": "/mnt/state/dev/hub/{unescaped_username}",
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
                {"name": "user-home", "mountPath": "/home/{unescaped_username}"},
                {"name": "user-global", "mountPath": "/global_share"},
            ]

            assert mock_config.KubeSpawner.volume_mounts == expected_volume_mounts

    def test_configure_hostpath_storage_with_prod_env(self):
        """Test that storage configuration works with production environment path."""
        # Mock configuration object
        mock_config = Mock()

        # Test with prod environment path
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_HOMES_DIR": "/mnt/state/prod/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify the user-home volume uses the prod path
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/mnt/state/prod/hub/{unescaped_username}"

            # Verify the user-global volume uses the prod path
            user_global_volume = mock_config.KubeSpawner.volumes[1]
            assert user_global_volume["hostPath"]["path"] == "/mnt/state/prod/hub/global_share"

    def test_configure_hostpath_storage_with_staging_env(self):
        """Test that storage configuration works with staging environment path."""
        # Mock configuration object
        mock_config = Mock()

        # Test with staging environment path
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_HOMES_DIR": "/mnt/state/staging/hub"}):
            configure_hostpath_storage(mock_config)

            # Verify the paths are correctly constructed
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/mnt/state/staging/hub/{unescaped_username}"

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
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_HOMES_DIR": "/custom/storage/path"}):
            configure_hostpath_storage(mock_config)

            # Verify the custom path is used
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert user_home_volume["hostPath"]["path"] == "/custom/storage/path/{unescaped_username}"

            user_global_volume = mock_config.KubeSpawner.volumes[1]
            assert user_global_volume["hostPath"]["path"] == "/custom/storage/path/global_share"

    def test_unescaped_username_avoids_hash_suffix(self):
        """
        Test that {unescaped_username} is used instead of {username} to avoid hash suffixes.

        This test demonstrates the difference between {username} and {unescaped_username}:
        - For DNS-compliant usernames like 'user123': both would be the same
        - For usernames with special characters like 'user_name':
          * {username} would become 'user-name---<hash>' (with hash suffix)
          * {unescaped_username} stays as 'user_name' (original, no hash)

        By using {unescaped_username}, we ensure consistent directory names
        that match the raw KBase username, regardless of DNS-1123 compliance.
        """
        from kubespawner.slugs import safe_slug

        # Test case 1: DNS-compliant username (lowercase alphanumeric only)
        dns_compliant = "user123"
        # For DNS-compliant usernames, safe_slug returns the name unchanged
        safe_result = safe_slug(dns_compliant)
        assert safe_result == "user123"
        # In this case, {username} and {unescaped_username} would be the same:
        # - {username} → "user123"
        # - {unescaped_username} → "user123"

        # Test case 2: Username with underscore (not DNS-compliant)
        username_with_special_char = "user_name"
        # For non-compliant usernames, safe_slug adds a hash suffix
        safe_result_with_hash = safe_slug(username_with_special_char)

        # Verify that safe_slug adds the hash suffix (pattern: name---hash)
        assert safe_result_with_hash.startswith("user-name---")
        assert len(safe_result_with_hash) == len("user-name---") + 8  # 8-char hash
        # The hash is deterministic (SHA-256 based), so it's always the same for "user_name"
        assert safe_result_with_hash == "user-name---2e0d0e00"

        # In this case, {username} and {unescaped_username} are DIFFERENT:
        # - {username} → "user-name---4544402c" (DNS-safe with hash)
        # - {unescaped_username} → "user_name" (original username, preserved as-is)
        #
        # Note: In KubeSpawner's template expansion (see spawner.py:2084):
        #   unescaped_username = self.user.name  # Always the raw username
        #   username = safe_username            # DNS-safe version (may have hash)
        #
        # This is why we use {unescaped_username} in storage.py:
        # - With {username}: home directory would be '/home/user-name---4544402c'
        # - With {unescaped_username}: home directory is '/home/user_name' (matches raw username)

        # Verify our configuration uses {unescaped_username} template string
        mock_config = Mock()
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_HOMES_DIR": "/mnt/state/dev/hub"}):
            configure_hostpath_storage(mock_config)

            # Check that the path template uses the string "{unescaped_username}"
            # (KubeSpawner will expand this to self.user.name at runtime)
            user_home_volume = mock_config.KubeSpawner.volumes[0]
            assert "{unescaped_username}" in user_home_volume["hostPath"]["path"]
            assert "{username}" not in user_home_volume["hostPath"]["path"]

            # Check that the mount path also uses "{unescaped_username}"
            user_home_mount = mock_config.KubeSpawner.volume_mounts[0]
            assert "{unescaped_username}" in user_home_mount["mountPath"]
            assert "{username}" not in user_home_mount["mountPath"]

            # Verify the full expected paths (as template strings, not expanded values)
            assert user_home_volume["hostPath"]["path"] == "/mnt/state/dev/hub/{unescaped_username}"
            assert user_home_mount["mountPath"] == "/home/{unescaped_username}"


if __name__ == "__main__":
    pytest.main([__file__])
