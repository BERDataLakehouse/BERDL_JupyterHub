# BERDL Notebook Image Configuration

This directory contains example configurations for dynamically updating the notebook image without redeploying JupyterHub.

## Method 1: Using Kubernetes Secret (Recommended)

Create a secret containing the notebook image tag:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: berdl-notebook-image-config
  namespace: jupyterhub-dev
type: Opaque
data:
  # Base64 encoded image tag: echo -n "ghcr.io/bio-boris/berdl_notebook:v2.0.0" | base64
  notebook-image-tag: Z2hjci5pby9iaW8tYm9yaXMvYmVyZGxfbm90ZWJvb2s6djIuMC4w
```

Then mount this secret in the JupyterHub deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: berdlhub
  namespace: jupyterhub-dev
spec:
  template:
    spec:
      containers:
      - name: berdlhub
        # ... other container configuration
        env:
        - name: BERDL_NOTEBOOK_IMAGE_TAG_FILE
          value: /etc/berdl/notebook-image-tag
        volumeMounts:
        - name: notebook-image-config
          mountPath: /etc/berdl
          readOnly: true
      volumes:
      - name: notebook-image-config
        secret:
          secretName: berdl-notebook-image-config
```

## Method 2: Using ConfigMap

Create a configmap containing the notebook image tag:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: berdl-notebook-image-config
  namespace: jupyterhub-dev
data:
  notebook-image-tag: "ghcr.io/bio-boris/berdl_notebook:v2.0.0"
```

Then mount this configmap in the JupyterHub deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: berdlhub
  namespace: jupyterhub-dev
spec:
  template:
    spec:
      containers:
      - name: berdlhub
        # ... other container configuration
        env:
        - name: BERDL_NOTEBOOK_IMAGE_TAG_FILE
          value: /etc/berdl/notebook-image-tag
        volumeMounts:
        - name: notebook-image-config
          mountPath: /etc/berdl
          readOnly: true
      volumes:
      - name: notebook-image-config
        configMap:
          name: berdl-notebook-image-config
```

## Updating the Notebook Image

To update the notebook image without redeploying JupyterHub:

### For Secrets:
```bash
# Update the secret with new image tag
kubectl patch secret berdl-notebook-image-config -n jupyterhub-dev \
  --patch='{"data":{"notebook-image-tag":"'"$(echo -n 'ghcr.io/bio-boris/berdl_notebook:v3.0.0' | base64)"'"}}'
```

### For ConfigMaps:
```bash
# Update the configmap with new image tag
kubectl patch configmap berdl-notebook-image-config -n jupyterhub-dev \
  --patch='{"data":{"notebook-image-tag":"ghcr.io/bio-boris/berdl_notebook:v3.0.0"}}'
```

## Configuration Options

| Environment Variable | Default Value | Description |
|---------------------|---------------|-------------|
| `BERDL_NOTEBOOK_IMAGE_TAG_FILE` | `/etc/berdl/notebook-image-tag` | Path to file containing notebook image tag |
| `BERDL_NOTEBOOK_IMAGE_TAG` | (required if file not found) | Fallback environment variable for notebook image tag |

## Behavior

1. JupyterHub first tries to read the notebook image tag from the mounted file
2. If the file doesn't exist or is empty, it falls back to the `BERDL_NOTEBOOK_IMAGE_TAG` environment variable
3. If neither source is available, JupyterHub will fail to start with an error
4. The image tag is read fresh each time a user spawns a new notebook server

## Notes

- Changes to the mounted file/secret/configmap take effect immediately for new notebook spawns
- Existing running notebooks continue to use their original image
- Users need to stop and restart their notebooks to get the new image
- Use secrets for sensitive image registries or private repositories
- Use configmaps for public repositories where the image tag is not sensitive