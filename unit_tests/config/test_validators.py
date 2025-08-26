"""Tests for environment validation."""

import os
from unittest.mock import patch
import pytest

from berdlhub.config.validators import validate_environment


class TestEnvironmentValidation:
    """Test cases for environment variable validation."""

    def test_validate_environment_with_berdl_notebook_homes_dir(self):
        """Test that validation passes when BERDL_NOTEBOOK_HOMES_DIR is set along with other required vars."""
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
            "BERDL_NOTEBOOK_HOMES_DIR": "/mnt/state/dev/hub",
        }

        with patch.dict(os.environ, required_env_vars, clear=True):
            # Mock logger to capture messages
            with patch("berdlhub.config.validators.logger") as mock_logger:
                # Should not raise an exception
                validate_environment()

                # Verify success message was logged
                mock_logger.info.assert_any_call("Environment validation successful!")

    def test_validate_environment_missing_berdl_notebook_homes_dir(self):
        """Test that validation fails when BERDL_NOTEBOOK_HOMES_DIR is missing."""
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
            # BERDL_NOTEBOOK_HOMES_DIR is intentionally missing
        }

        with patch.dict(os.environ, required_env_vars, clear=True):
            with patch("berdlhub.config.validators.logger") as mock_logger:
                with pytest.raises(SystemExit) as exc_info:
                    validate_environment()

                # Verify it exits with status 1
                assert exc_info.value.code == 1

                # Verify error message includes BERDL_NOTEBOOK_HOMES_DIR
                mock_logger.error.assert_any_call("Missing required environment variables:")
                # Check that the second error call contains our missing variable
                error_calls = mock_logger.error.call_args_list
                assert len(error_calls) >= 2
                missing_vars_message = error_calls[1][0][0]  # Second call, first argument
                assert "BERDL_NOTEBOOK_HOMES_DIR" in missing_vars_message

    def test_validate_environment_berdl_notebook_homes_dir_in_required_vars(self):
        """Test that BERDL_NOTEBOOK_HOMES_DIR is correctly included in required variables."""
        # This test ensures our addition to the required_vars dict is correct
        from berdlhub.config.validators import validate_environment
        import inspect

        # Get the source code of the function to verify BERDL_NOTEBOOK_HOMES_DIR is listed
        source = inspect.getsource(validate_environment)
        assert "BERDL_NOTEBOOK_HOMES_DIR" in source
        assert "Base path for hub storage" in source


if __name__ == "__main__":
    pytest.main([__file__])
