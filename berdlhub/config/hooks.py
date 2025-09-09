import os
import re

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


def _get_profile_environment(spawner) -> dict:
    """Extract environment variables from the selected profile."""
    profile_list = spawner.profile_list or []

    if not profile_list:
        return {}

    selected_profile = None
    profile_slug = None

    # Get the profile slug from user_options
    if spawner.user_options and "profile" in spawner.user_options:
        profile_slug = spawner.user_options["profile"]

        # Find the profile by matching the slug
        for i, profile in enumerate(profile_list):
            # JupyterHub generates slugs from display_name by converting to lowercase
            # and replacing spaces/special chars with dashes
            #
            # Examples from real profile display_names:
            # "Small: 1 Worker (2GB, 1 core) + Master (1GB, 1 core)"
            #   -> "small-1-worker-2gb-1-core-master-1gb-1-core"
            # "Medium: 4 Workers (8GB, 1 core each) + Master (8GB, 1 core)"
            #   -> "medium-4-workers-8gb-1-core-each-master-8gb-1-core"
            # "Large: 4 Workers (32GB, 1 core each) + Master (16GB, 1 core)"
            #   -> "large-4-workers-32gb-1-core-each-master-16gb-1-core"
            display_name = profile.get("display_name", "")

            generated_slug = (
                display_name.lower()  # Convert to lowercase
                .replace(" ", "-")  # Spaces become dashes
                .replace("(", "")  # Remove opening parentheses
                .replace(")", "")  # Remove closing parentheses
                .replace(",", "")  # Remove commas
                .replace("+", "-")  # Plus signs become dashes
                .replace(":", "")  # Remove colons
            )
            # Remove consecutive dashes (e.g., "each--master" -> "each-master")
            generated_slug = re.sub(r"-+", "-", generated_slug)

            spawner.log.info(f"DEBUG: Profile {i}: display_name='{display_name}', generated_slug='{generated_slug}'")

            if generated_slug == profile_slug:
                selected_profile = profile
                break

    # Default to first profile if no match found
    if selected_profile is None:
        selected_profile = profile_list[0]

    kubespawner_override = selected_profile.get("kubespawner_override", {})
    profile_environment = kubespawner_override.get("environment", {})

    return profile_environment


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

    # Get profile-specific environment from selected profile
    profile_env = _get_profile_environment(spawner)

    # Merge spawner environment with profile environment
    merged_env = {**spawner.environment, **profile_env}

    await SparkClusterManager(kb_auth_token, environment=merged_env).start_spark_cluster(spawner)


async def post_stop_hook(spawner):
    """
    Hook to delete the Spark cluster after the user's server stops.
    """
    kb_auth_token = await _get_auth_token(spawner)
    spawner.log.debug("Post-stop hook called for user %s", spawner.user.name)
    if os.environ["BERDL_SKIP_SPAWN_HOOKS"].lower() == "true":
        spawner.log.info("Skipping post-stop hook due to BERDL_SKIP_SPAWN_HOOKS environment variable.")
        return
    # Get profile-specific environment for consistency
    profile_env = _get_profile_environment(spawner)
    merged_env = {**spawner.environment, **profile_env}
    await SparkClusterManager(kb_auth_token, environment=merged_env).stop_spark_cluster(spawner)


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

    # Add tolerations if specified
    tolerations_env = os.environ.get("BERDL_TOLERATIONS")
    if tolerations_env:
        tolerations = parse_tolerations_from_env(tolerations_env, spawner)
        if tolerations:
            pod.spec.tolerations = tolerations

    return pod


def parse_tolerations_from_env(tolerations_env: str, spawner) -> list[client.V1Toleration]:
    """
    Parse tolerations from a comma-separated environment variable string.
    Each toleration should be in the format: key=value:effect
    Example: key1=value1:NoSchedule,key2=value2:PreferNoSchedule
    """
    tolerations = []
    for toleration_str in tolerations_env.split(","):
        toleration_str = toleration_str.strip()
        if not toleration_str:
            continue

        try:
            if ":" not in toleration_str or "=" not in toleration_str:
                raise ValueError("Missing ':' or '=' in toleration format")

            key_value, effect = toleration_str.split(":", 1)
            key, value = key_value.split("=", 1)
            tolerations.append(client.V1Toleration(key=key, operator="Equal", value=value, effect=effect))
        except ValueError:
            spawner.log.warning(f"Invalid toleration format: {toleration_str}. Expected format: key=value:effect")
    return tolerations


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
                    "ln -sfn /global_share /home/$NB_USER/global_share || true",
                ]
            }
        }
    }
