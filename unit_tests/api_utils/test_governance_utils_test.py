import os
from unittest.mock import Mock, patch

import httpx
import pytest

from berdlhub.api_utils.governance_utils import GovernanceUtils


class TestGovernanceUtils:
    """Test suite for GovernanceUtils class."""

    def test_init(self):
        """Test initialization with auth token."""
        token = "test_token_123"
        utils = GovernanceUtils(token)
        assert utils.kbase_auth_token == token

    @pytest.mark.asyncio
    async def test_set_governance_credentials_success(self):
        """Test successful credential retrieval and spawner update."""
        # Setup
        token = "test_token"
        utils = GovernanceUtils(token)

        # Mock spawner
        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        # Mock response data
        mock_creds = {"access_key": "test_access_key", "secret_key": "test_secret_key"}

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "True",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                # Configure mock response
                mock_response = Mock()
                mock_response.json.return_value = mock_creds
                mock_response.raise_for_status.return_value = None

                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                # Execute
                await utils.set_governance_credentials(spawner)

                # Verify HTTP request
                mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                    "https://gov.example.com/credentials/",
                    headers={"Authorization": "Bearer test_token"},
                )

                # Verify spawner environment
                expected_env = {
                    "MINIO_ACCESS_KEY": "test_access_key",
                    "MINIO_SECRET_KEY": "test_secret_key",
                    "MINIO_ENDPOINT": "https://minio.example.com",
                    "MINIO_SECURE": "True",
                }
                assert spawner.environment == expected_env

                # Verify error key removed
                assert "MINIO_CONFIG_ERROR" not in spawner.environment

                # Verify logging
                spawner.log.info.assert_called_once_with("Successfully set MinIO credentials for user %s.", "test_user")

    @pytest.mark.asyncio
    async def test_set_governance_credentials_with_default_secure_flag(self):
        """Test successful credential retrieval with default MINIO_SECURE_FLAG."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        mock_creds = {"access_key": "key", "secret_key": "secret"}

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                # MINIO_SECURE_FLAG not set
            },
            clear=True,
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = mock_creds
                mock_response.raise_for_status.return_value = None
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await utils.set_governance_credentials(spawner)

                # Should use default "True"
                assert spawner.environment["MINIO_SECURE"] == "True"

    @pytest.mark.asyncio
    async def test_set_governance_credentials_http_error(self):
        """Test handling of HTTP errors."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "False",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                # Configure mock to raise HTTP error
                mock_response = Mock()
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401 Unauthorized", request=Mock(), response=Mock()
                )
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await utils.set_governance_credentials(spawner)

                # Verify error environment
                expected_env = {
                    "MINIO_ACCESS_KEY": "",
                    "MINIO_SECRET_KEY": "",
                    "MINIO_ENDPOINT": "",
                    "MINIO_SECURE": "False",
                    "MINIO_CONFIG_ERROR": "Failed to retrieve MinIO credentials. Please contact an administrator.",
                }
                assert spawner.environment == expected_env

                # Verify error logging
                spawner.log.error.assert_called_once()
                error_call = spawner.log.error.call_args
                assert error_call[0][0] == "Failed to get governance credentials for user %s: %s"
                assert error_call[0][1] == "test_user"

    @pytest.mark.asyncio
    async def test_set_governance_credentials_missing_env_var(self):
        """Test handling of missing environment variables."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            await utils.set_governance_credentials(spawner)

            # Verify error environment
            expected_env = {
                "MINIO_ACCESS_KEY": "",
                "MINIO_SECRET_KEY": "",
                "MINIO_ENDPOINT": "",
                "MINIO_SECURE": "False",
                "MINIO_CONFIG_ERROR": "Failed to retrieve MinIO credentials. Please contact an administrator.",
            }
            assert spawner.environment == expected_env

            # Verify error logging
            spawner.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_governance_credentials_json_decode_error(self):
        """Test handling of JSON decode errors."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "True",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.side_effect = ValueError("Invalid JSON")
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await utils.set_governance_credentials(spawner)

                # Verify error environment
                error_msg = "Failed to retrieve MinIO credentials. Please contact an administrator."
                assert spawner.environment["MINIO_CONFIG_ERROR"] == error_msg
                spawner.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_governance_credentials_removes_existing_error(self):
        """Test that existing MINIO_CONFIG_ERROR is removed on success."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {"MINIO_CONFIG_ERROR": "Previous error"}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        mock_creds = {"access_key": "key", "secret_key": "secret"}

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "True",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = mock_creds
                mock_response.raise_for_status.return_value = None
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await utils.set_governance_credentials(spawner)

                # Verify error key is removed
                assert "MINIO_CONFIG_ERROR" not in spawner.environment

    @pytest.mark.asyncio
    async def test_set_governance_credentials_network_timeout(self):
        """Test handling of network timeouts."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {}
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "True",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

                await utils.set_governance_credentials(spawner)

                # Verify error handling
                error_msg = "Failed to retrieve MinIO credentials. Please contact an administrator."
                assert spawner.environment["MINIO_CONFIG_ERROR"] == error_msg
                spawner.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_governance_credentials_preserves_other_env_vars(self):
        """Test that other environment variables are preserved."""
        token = "test_token"
        utils = GovernanceUtils(token)

        spawner = Mock()
        spawner.environment = {
            "OTHER_VAR": "preserved_value",
            "ANOTHER_VAR": "also_preserved",
        }
        spawner.log = Mock()
        spawner.user = Mock()
        spawner.user.name = "test_user"

        mock_creds = {"access_key": "key", "secret_key": "secret"}

        with patch.dict(
            os.environ,
            {
                "GOVERNANCE_API_URL": "https://gov.example.com",
                "MINIO_ENDPOINT_URL": "https://minio.example.com",
                "MINIO_SECURE_FLAG": "True",
            },
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = mock_creds
                mock_response.raise_for_status.return_value = None
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await utils.set_governance_credentials(spawner)

                # Verify other vars preserved
                assert spawner.environment["OTHER_VAR"] == "preserved_value"
                assert spawner.environment["ANOTHER_VAR"] == "also_preserved"
                assert spawner.environment["MINIO_ACCESS_KEY"] == "key"
