"""
Configuration for creating Kubernetes Services for user notebooks.

This module provides helper functions to create Services for user notebook pods,
enabling external access to the Spark Connect server running inside the notebook.

IMPORTANT: This module must be imported BEFORE hooks.py in the configuration loading order,
as hooks.py will wrap these service management functions.
"""

import re
from kubernetes import client, config


def sanitize_k8s_name(name: str) -> str:
    """
    Sanitize a string to be Kubernetes DNS-1123 subdomain compliant.

    Kubernetes resource names must:
    - Consist of lowercase alphanumeric characters, '-', or '.'
    - Start and end with an alphanumeric character
    - Be at most 253 characters long

    Args:
        name: The string to sanitize (e.g., username with underscores)

    Returns:
        A DNS-1123 compliant string (replaces underscores with hyphens)
    """
    # Replace underscores and other invalid characters with hyphens
    sanitized = re.sub(r"[^a-z0-9.-]", "-", name.lower())

    # Ensure it starts and ends with alphanumeric
    sanitized = re.sub(r"^[^a-z0-9]+", "", sanitized)
    sanitized = re.sub(r"[^a-z0-9]+$", "", sanitized)

    # Collapse multiple consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)

    # Truncate to 253 characters (K8s limit)
    return sanitized[:253]


def create_user_notebook_service(spawner):
    """
    Create a Kubernetes Service for the user's notebook pod.

    This allows the Spark Connect server (running on port 15002) to be accessed
    from other pods via DNS:

        sc://jupyter-{username}.{namespace}:15002

    Args:
        spawner: KubeSpawner instance

    Returns:
        None (creates service via Kubernetes API)
    """
    username = spawner.user.name
    namespace = spawner.namespace
    # Sanitize username for Kubernetes DNS-1123 compliance (replace underscores with hyphens)
    sanitized_username = sanitize_k8s_name(username)
    service_name = f"jupyter-{sanitized_username}"

    # Match the labels on the pod created by KubeSpawner
    selector_labels = {
        "app": "berdl-notebook",
        "component": "singleuser-server",
        "hub.jupyter.org/username": username,
    }

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=service_name,
            namespace=namespace,
            labels={
                **selector_labels,
                "app.kubernetes.io/managed-by": "jupyterhub",
            },
            annotations={
                "description": f"Service for {username}'s notebook and Spark Connect server",
            },
        ),
        spec=client.V1ServiceSpec(
            type="ClusterIP",
            selector=selector_labels,
            ports=[
                # JupyterLab port
                client.V1ServicePort(
                    name="notebook",
                    port=8888,
                    target_port=8888,
                    protocol="TCP",
                ),
                # Spark Connect port
                client.V1ServicePort(
                    name="spark-connect",
                    port=15002,
                    target_port=15002,
                    protocol="TCP",
                ),
            ],
        ),
    )

    # Create or update the service using Kubernetes API
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        # Try to get existing service
        try:
            v1.read_namespaced_service(name=service_name, namespace=namespace)
            # Service exists, patch it
            v1.patch_namespaced_service(name=service_name, namespace=namespace, body=service)
            spawner.log.info(f"✅ Updated Service {service_name}.{namespace}")
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # Service doesn't exist, create it
                v1.create_namespaced_service(namespace=namespace, body=service)
                spawner.log.info(f"✅ Created Service {service_name}.{namespace}")
                spawner.log.info(f"   - Jupyter: http://{service_name}.{namespace}:8888")
                spawner.log.info(f"   - Spark Connect: sc://{service_name}.{namespace}:15002")
            else:
                raise
    except Exception as e:
        spawner.log.error(f"❌ Failed to create/update Service {service_name}: {e}")
        # Don't fail pod creation if service creation fails


def delete_user_notebook_service(spawner):
    """
    Delete the Kubernetes Service for the user's notebook pod.

    Args:
        spawner: KubeSpawner instance

    Returns:
        None (deletes service via Kubernetes API)
    """
    username = spawner.user.name
    # Sanitize username for Kubernetes DNS-1123 compliance (replace underscores with hyphens)
    sanitized_username = sanitize_k8s_name(username)
    service_name = f"jupyter-{sanitized_username}"

    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        v1.delete_namespaced_service(name=service_name, namespace=spawner.namespace)
        spawner.log.info(f"🗑️  Deleted Service {service_name}")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            spawner.log.info(f"Service {service_name} already deleted")
        else:
            spawner.log.error(f"Failed to delete Service {service_name}: {e}")
    except Exception as e:
        spawner.log.error(f"Unexpected error deleting Service: {e}")


def ensure_pod_labels_for_service(spawner, pod):
    """
    Ensure the pod has the required labels for Service selection.

    Args:
        spawner: KubeSpawner instance
        pod: V1Pod object to modify

    Returns:
        Modified V1Pod object
    """
    username = spawner.user.name

    if not pod.metadata.labels:
        pod.metadata.labels = {}

    pod.metadata.labels.update(
        {
            "app": "berdl-notebook",
            "component": "singleuser-server",
            "hub.jupyter.org/username": username,
        }
    )

    return pod
