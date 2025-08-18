import os
import httpx


class GovernanceUtils:
    """
    A utility class to manage MinIO credentials for a JupyterHub spawner.
    """

    def __init__(self, kbase_auth_token: str):
        """
        Initialize the GovernanceUtils with a KBase authentication token.

        Args:
            kbase_auth_token (str): The KBase authentication token for the user.
        """
        self.kbase_auth_token = kbase_auth_token

    async def set_governance_credentials(self, spawner) -> None:
        """Main method to fetch credentials and update the spawner's environment."""
        try:
            # Get config from environment
            gov_url = os.environ["GOVERNANCE_API_URL"]
            minio_endpoint = os.environ["MINIO_ENDPOINT_URL"]
            minio_secure = os.environ.get("MINIO_SECURE_FLAG", "True")

            # Fetch credentials
            headers = {"Authorization": f"Bearer {self.kbase_auth_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{gov_url}/credentials/", headers=headers)
                response.raise_for_status()
                creds = response.json()

            # Set successful credentials
            spawner.environment.update(
                {
                    "MINIO_ACCESS_KEY": creds["access_key"],
                    "MINIO_SECRET_KEY": creds["secret_key"],
                    "MINIO_ENDPOINT": minio_endpoint,
                    "MINIO_SECURE": minio_secure,
                }
            )
            spawner.environment.pop("MINIO_CONFIG_ERROR", None)

            spawner.log.info("Successfully set MinIO credentials for user %s.", spawner.user.name)

        except Exception as e:
            # Graceful failure - set empty credentials with an error message
            spawner.log.error(
                "Failed to get governance credentials for user %s: %s",
                spawner.user.name,
                str(e),
                exc_info=True,
            )

            spawner.environment.update(
                {
                    "MINIO_ACCESS_KEY": "",
                    "MINIO_SECRET_KEY": "",
                    "MINIO_ENDPOINT": "",
                    "MINIO_SECURE": "False",
                    "MINIO_CONFIG_ERROR": "Failed to retrieve MinIO credentials. Please contact an administrator.",
                }
            )
