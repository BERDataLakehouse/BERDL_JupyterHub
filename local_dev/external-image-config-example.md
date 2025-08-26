# Example: Using external notebook image configuration in local development

This example shows how to test the external notebook image configuration feature in your local development environment.

## Option 1: Using a Secret (Recommended)

Create a secret containing the notebook image tag:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: berdl-notebook-image-config
  namespace: jupyterhub-dev
type: Opaque
data:
  # Base64 encoded: ghcr.io/bio-boris/berdl_notebook:main
  notebook-image-tag: Z2hjci5pby9iaW8tYm9yaXMvYmVyZGxfbm90ZWJvb2s6bWFpbg==
```

Apply the secret:
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: berdl-notebook-image-config
  namespace: jupyterhub-dev
type: Opaque
data:
  notebook-image-tag: Z2hjci5pby9iaW8tYm9yaXMvYmVyZGxfbm90ZWJvb2s6bWFpbg==
EOF
```

Then modify the `hub.yaml` to mount this secret by adding the volumeMounts and volumes sections:

```yaml
# Add to containers[0].env:
- name: BERDL_NOTEBOOK_IMAGE_TAG_FILE
  value: /etc/berdl/notebook-image-tag

# Add to containers[0].volumeMounts:
- name: notebook-image-config
  mountPath: /etc/berdl
  readOnly: true

# Add to spec.template.spec.volumes:
- name: notebook-image-config
  secret:
    secretName: berdl-notebook-image-config
```

## Option 2: Using a ConfigMap

Create a configmap:

```bash
kubectl create configmap berdl-notebook-image-config \
  --from-literal=notebook-image-tag="ghcr.io/bio-boris/berdl_notebook:main" \
  -n jupyterhub-dev
```

Then modify the `hub.yaml` similar to above, but use a configMap volume instead:

```yaml
# Add to spec.template.spec.volumes:
- name: notebook-image-config
  configMap:
    name: berdl-notebook-image-config
```

## Testing the Configuration

1. Deploy with the new configuration:
   ```bash
   kubectl apply -k local_dev/
   ```

2. Test updating the image without redeploying:
   ```bash
   # Update to a different tag
   kubectl patch secret berdl-notebook-image-config -n jupyterhub-dev \
     --patch='{"data":{"notebook-image-tag":"'"$(echo -n 'ghcr.io/bio-boris/berdl_notebook:latest' | base64)"'"}}'
   ```

3. Check the logs to see the image being read from the file:
   ```bash
   kubectl logs -n jupyterhub-dev deployment/berdlhub
   ```

4. Spawn a new notebook to test that it uses the updated image

## Fallback Testing

To test the fallback to environment variables, you can:

1. Remove the mounted file path environment variable or
2. Delete the secret/configmap and ensure the system falls back to `BERDL_NOTEBOOK_IMAGE_TAG`