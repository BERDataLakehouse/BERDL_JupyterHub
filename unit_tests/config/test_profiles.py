"""Tests for profiles configuration."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from berdlhub.config.profiles import _get_notebook_image_tag, configure_profiles


class TestGetNotebookImageTag:
    """Test the _get_notebook_image_tag function."""

    def test_reads_from_file_when_exists(self):
        """Test that it reads from mounted file when available."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test-image:v1.0.0")
            f.flush()

            try:
                with patch.dict(os.environ, {"BERDL_NOTEBOOK_IMAGE_TAG_FILE": f.name}):
                    result = _get_notebook_image_tag()
                    assert result == "test-image:v1.0.0"
            finally:
                os.unlink(f.name)

    def test_strips_whitespace_from_file(self):
        """Test that whitespace is stripped from file content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("  test-image:v1.0.0\n  ")
            f.flush()

            try:
                with patch.dict(os.environ, {"BERDL_NOTEBOOK_IMAGE_TAG_FILE": f.name}):
                    result = _get_notebook_image_tag()
                    assert result == "test-image:v1.0.0"
            finally:
                os.unlink(f.name)

    def test_falls_back_to_env_var_when_file_not_exists(self):
        """Test fallback to environment variable when file doesn't exist."""
        with patch.dict(
            os.environ,
            {"BERDL_NOTEBOOK_IMAGE_TAG_FILE": "/nonexistent/file", "BERDL_NOTEBOOK_IMAGE_TAG": "env-image:v2.0.0"},
        ):
            result = _get_notebook_image_tag()
            assert result == "env-image:v2.0.0"

    def test_falls_back_to_env_var_when_file_empty(self):
        """Test fallback to environment variable when file is empty."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("")
            f.flush()

            try:
                with patch.dict(
                    os.environ,
                    {"BERDL_NOTEBOOK_IMAGE_TAG_FILE": f.name, "BERDL_NOTEBOOK_IMAGE_TAG": "env-image:v2.0.0"},
                ):
                    result = _get_notebook_image_tag()
                    assert result == "env-image:v2.0.0"
            finally:
                os.unlink(f.name)

    def test_uses_default_file_path_when_env_not_set(self):
        """Test that it uses default file path when BERDL_NOTEBOOK_IMAGE_TAG_FILE is not set."""
        with patch.dict(os.environ, {"BERDL_NOTEBOOK_IMAGE_TAG": "env-image:v2.0.0"}, clear=True):
            # Mock os.path.exists to return False for default path
            with patch("os.path.exists", return_value=False):
                result = _get_notebook_image_tag()
                assert result == "env-image:v2.0.0"

    def test_raises_error_when_no_source_available(self):
        """Test that it raises error when neither file nor env var is available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(
                    ValueError, match="Neither BERDL_NOTEBOOK_IMAGE_TAG_FILE nor BERDL_NOTEBOOK_IMAGE_TAG is available"
                ):
                    _get_notebook_image_tag()

    def test_handles_file_read_error_gracefully(self):
        """Test that file read errors are handled gracefully with fallback."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.close()

            try:
                # Make file unreadable
                os.chmod(f.name, 0o000)

                with patch.dict(
                    os.environ,
                    {"BERDL_NOTEBOOK_IMAGE_TAG_FILE": f.name, "BERDL_NOTEBOOK_IMAGE_TAG": "env-image:v2.0.0"},
                ):
                    result = _get_notebook_image_tag()
                    assert result == "env-image:v2.0.0"
            finally:
                # Restore permissions and delete
                os.chmod(f.name, 0o644)
                os.unlink(f.name)


class TestConfigureProfiles:
    """Test the configure_profiles function."""

    def test_configure_profiles_uses_image_tag(self):
        """Test that configure_profiles uses the image tag from _get_notebook_image_tag."""
        mock_config = MagicMock()

        with patch("berdlhub.config.profiles._get_notebook_image_tag", return_value="test-image:v1.0.0"):
            configure_profiles(mock_config)

            # Verify that profile_list was set
            assert hasattr(mock_config.KubeSpawner, "profile_list")
            profiles = mock_config.KubeSpawner.profile_list

            # Check that all profiles use the correct image
            for profile in profiles:
                assert profile["kubespawner_override"]["image"] == "test-image:v1.0.0"

            # Verify we have the expected number of profiles
            assert len(profiles) == 3

            # Verify profile names
            profile_names = [p["display_name"] for p in profiles]
            expected_names = [
                "Small Server (2G RAM, 1 CPU)",
                "Medium Server (8G RAM, 2 CPU)",
                "Large Server (32G RAM, 4 CPU)",
            ]
            assert profile_names == expected_names
