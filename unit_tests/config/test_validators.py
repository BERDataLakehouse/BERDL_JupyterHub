"""Tests for environment validation."""

import os
from unittest.mock import patch
import pytest

from berdlhub.config.validators import validate_environment


class TestEnvironmentValidation:
    """Test cases for environment variable validation."""

    def test_validate_environment_all_required_vars(self):
        """Test that validation passes when all required vars are set."""
        required_env_vars = {
            "JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS": "test_secret_64_chars_long_string_here_for_testing_purposes",
            "JUPYTERHUB_TEMPLATES_DIR": "/path/to/templates",
            "KBASE_ORIGIN": "https://kbase.us",
            "KBASE_AUTH_URL": "https://auth.kbase.us",
            "CDM_TASK_SERVICE_URL": "https://cdm.kbase.us",
            "GOVERNANCE_API_URL": "https://governance.kbase.us",
            "MINIO_ENDPOINT_URL": "https://minio.kbase.us",
            "SPARK_CLUSTER_MANAGER_API_URL": "https://spark.kbase.us",
            "BERDL_HIVE_METASTORE_URI": "thrift://hive:9083",
            "BERDL_NOTEBOOK_IMAGE_TAG": "latest",
            "BERDL_SKIP_SPAWN_HOOKS": "false",
        }

        with patch.dict(os.environ, required_env_vars, clear=True):
            with patch("berdlhub.config.validators.logger") as mock_logger:
                validate_environment()
                mock_logger.info.assert_any_call("Environment validation successful!")

    def test_validate_environment_no_berdl_notebook_homes_dir_needed(self):
        """Test that BERDL_NOTEBOOK_HOMES_DIR is NOT required (removed for S3 FUSE storage)."""
        required_env_vars = {
            "JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS": "test_secret_64_chars_long_string_here_for_testing_purposes",
            "JUPYTERHUB_TEMPLATES_DIR": "/path/to/templates",
            "KBASE_ORIGIN": "https://kbase.us",
            "KBASE_AUTH_URL": "https://auth.kbase.us",
            "CDM_TASK_SERVICE_URL": "https://cdm.kbase.us",
            "GOVERNANCE_API_URL": "https://governance.kbase.us",
            "MINIO_ENDPOINT_URL": "https://minio.kbase.us",
            "SPARK_CLUSTER_MANAGER_API_URL": "https://spark.kbase.us",
            "BERDL_HIVE_METASTORE_URI": "thrift://hive:9083",
            "BERDL_NOTEBOOK_IMAGE_TAG": "latest",
            "BERDL_SKIP_SPAWN_HOOKS": "false",
            # BERDL_NOTEBOOK_HOMES_DIR intentionally absent — no longer required
        }

        with patch.dict(os.environ, required_env_vars, clear=True):
            with patch("berdlhub.config.validators.logger") as mock_logger:
                # Should pass without BERDL_NOTEBOOK_HOMES_DIR
                validate_environment()
                mock_logger.info.assert_any_call("Environment validation successful!")


if __name__ == "__main__":
    pytest.main([__file__])
