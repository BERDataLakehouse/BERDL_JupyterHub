import os

from kubernetes import client

from berdlhub.api_utils.spark_utils import SparkClusterManager
from berdlhub.config.spark_connect_service import (
    create_user_notebook_service,
    delete_user_notebook_service,
    ensure_pod_labels_for_service,
)


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

        # Find the profile by matching the explicit slug
        for profile in profile_list:
            explicit_slug = profile.get("slug")
            if explicit_slug and explicit_slug == profile_slug:
                selected_profile = profile
                spawner.log.info(f"Profile matched by slug: {explicit_slug}")
                break

        # Log if no matching profile found
        if selected_profile is None:
            available_slugs = [p.get("slug") for p in profile_list]
            spawner.log.info(f"No profile found with slug '{profile_slug}'. Available profiles: {available_slugs}")

    # Default to first profile if no match found
    if selected_profile is None:
        selected_profile = profile_list[0]
        spawner.log.info(f"Using default profile: {selected_profile.get('display_name')}")

    kubespawner_override = selected_profile.get("kubespawner_override", {})
    profile_environment = kubespawner_override.get("environment", {})

    return profile_environment


async def pre_spawn_hook(spawner):
    """
    Hook to create a Spark cluster and Kubernetes Service before the user's server starts.
    """
    spawner.log.debug("Pre-spawn hook called for user %s", spawner.user.name)
    kb_auth_token = await _get_auth_token(spawner)
    if os.environ["BERDL_SKIP_SPAWN_HOOKS"].lower() == "true":
        spawner.log.info("Skipping pre-spawn hook due to BERDL_SKIP_SPAWN_HOOKS environment variable.")
        return

    # Get profile-specific environment from selected profile
    profile_env = _get_profile_environment(spawner)
    spawner.environment.update(profile_env)

    # Note: SparkClusterManager now handles cluster configuration internally via profile detection
    await SparkClusterManager(kb_auth_token).start_spark_cluster(spawner)

    # Create Kubernetes Service for Spark Connect access
    # This allows external pods (like datalake-mcp-server) to connect to the user's
    # Spark Connect server via DNS: sc://jupyter-{username}.{namespace}:15002
    spawner.log.info("Creating Kubernetes Service for Spark Connect access")
    create_user_notebook_service(spawner)


async def post_stop_hook(spawner):
    """
    Hook to delete the Spark cluster and Kubernetes Service after the user's server stops.
    """
    kb_auth_token = await _get_auth_token(spawner)
    spawner.log.debug("Post-stop hook called for user %s", spawner.user.name)
    if os.environ["BERDL_SKIP_SPAWN_HOOKS"].lower() == "true":
        spawner.log.info("Skipping post-stop hook due to BERDL_SKIP_SPAWN_HOOKS environment variable.")
        return
    # Get profile-specific environment for consistency
    profile_env = _get_profile_environment(spawner)
    spawner.environment.update(profile_env)
    await SparkClusterManager(kb_auth_token).stop_spark_cluster(spawner)

    # Delete Kubernetes Service
    spawner.log.info("Deleting Kubernetes Service for Spark Connect")
    delete_user_notebook_service(spawner)


def modify_pod_hook(spawner, pod):
    # Ensure pod has the correct labels for Service selection
    # This must be done BEFORE the Service is created in pre_spawn_hook
    pod = ensure_pod_labels_for_service(spawner, pod)

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
