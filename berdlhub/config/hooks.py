import os

from kubernetes import client

from berdlhub.api_utils.governance_utils import GovernanceUtils
from berdlhub.api_utils.spark_utils import SparkClusterManager


async def _get_auth_token(spawner) -> str:
    """Helper method to retrieve and validate the auth token from the user's auth_state."""
    auth_state = await spawner.user.get_auth_state()
    if not auth_state:
        spawner.log.error("KBase auth_state not found for user.")
        raise RuntimeError("KBase authentication state is missing.")

    kb_auth_token: str | None = auth_state.get("kbase_token")
    if not kb_auth_token:
        spawner.log.error("KBase token not found in auth_state.")
        raise RuntimeError("KBase authentication token is missing from auth_state.")
    return kb_auth_token


async def pre_spawn_hook(spawner):
    """
    Hook to create a Spark cluster before the user's server starts.
    """
    spawner.log.debug("Pre-spawn hook called for user %s", spawner.user.name)
    kb_auth_token = await _get_auth_token(spawner)
    if os.environ["BERDL_SKIP_SPAWN_HOOKS"].lower() == "true":
        spawner.log.info("Skipping pre-spawn hook due to BERDL_SKIP_SPAWN_HOOKS environment variable.")
        return

    await GovernanceUtils(kb_auth_token).set_governance_credentials(spawner)
    await SparkClusterManager(kb_auth_token).start_spark_cluster(spawner)


async def post_stop_hook(spawner):
    """
    Hook to delete the Spark cluster after the user's server stops.
    """
    kb_auth_token = await _get_auth_token(spawner)
    spawner.log.debug("Post-stop hook called for user %s", spawner.user.name)
    if os.environ["BERDL_SKIP_SPAWN_HOOKS"].lower() == "true":
        spawner.log.info("Skipping post-stop hook due to BERDL_SKIP_SPAWN_HOOKS environment variable.")
        return
    await SparkClusterManager(kb_auth_token).stop_spark_cluster(spawner)


def modify_pod_hook(spawner, pod):
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_POD_IP",
            None,
            client.V1EnvVarSource(field_ref=client.V1ObjectFieldSelector(field_path="status.podIP")),
        )
    )
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_POD_NAME",
            None,
            client.V1EnvVarSource(field_ref=client.V1ObjectFieldSelector(field_path="metadata.name")),
        )
    )
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_CPU_REQUEST",
            None,
            client.V1EnvVarSource(resource_field_ref=client.V1ResourceFieldSelector(resource="requests.cpu")),
        )
    )
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_CPU_LIMIT",
            None,
            client.V1EnvVarSource(resource_field_ref=client.V1ResourceFieldSelector(resource="limits.cpu")),
        )
    )
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_MEMORY_REQUEST",
            None,
            client.V1EnvVarSource(resource_field_ref=client.V1ResourceFieldSelector(resource="requests.memory")),
        )
    )
    pod.spec.containers[0].env.append(
        client.V1EnvVar(
            "BERDL_MEMORY_LIMIT",
            None,
            client.V1EnvVarSource(resource_field_ref=client.V1ResourceFieldSelector(resource="limits.memory")),
        )
    )

    return pod


def configure_hooks(c):
    c.KubeSpawner.pre_spawn_hook = pre_spawn_hook
    c.KubeSpawner.post_stop_hook = post_stop_hook
    c.KubeSpawner.modify_pod_hook = modify_pod_hook

    # Use the NB_USER environment variable that's already set
    c.KubeSpawner.lifecycle_hooks = {
        "postStart": {
            "exec": {
                "command": [
                    "/bin/sh",
                    "-c",
                    "ln -sfn /global_share /home/$NB_USER/global_share || true; "
                    'if [ ! -z "$MINIO_CREDS_JSON" ]; then '
                    'echo "$MINIO_CREDS_JSON" > /home/$NB_USER/minio_creds.json && '
                    "chown $NB_UID:$NB_GID /home/$NB_USER/minio_creds.json; "
                    "fi",
                ]
            }
        }
    }
