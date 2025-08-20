# BERDL JupyterHub Local Development

Deploy a local JupyterHub instance for BERDL development using Kubernetes.

## Info
* Deploy Kubernetes resources into your local cluster, such as Rancher Desktop
* These were adapted from https://gitlab.kbase.lbl.gov/berdl/configmaps and https://gitlab.kbase.lbl.gov/berdl/manifests using `kustomize build . | pbcopy` within the directory to copy the k8 resources 

## Deployment

### Option 1: Using Pre-built Images (Recommended for Testing)

```bash
kubectl apply -k local_dev/
```

This uses the existing GitHub Container Registry images specified in the configuration files.

### Option 2: Using Local Development Images

If you want to test your local changes:

1. **Build the image locally:**
   ```bash
   docker build -t berdl-jupyterhub:local .
   ```

2. **Update hub.yaml to use your local image:**
   ```yaml
   # In hub.yaml line 98, change:
   image: ghcr.io/berdatalakehouse/berdl_jupyterhub:pr-3
   # To:
   image: berdl-jupyterhub:local
   ```

3. **Deploy:**
   ```bash
   kubectl apply -k local_dev/
   ```

### Alternative: Copy to Rancher UI
* You can also copy them into the rancher2 UI to deploy them. Run `kustomize build . | pbcopy` to copy them to your clipboard.

## Configuration Files

### [configmap.yaml](configmap.yaml)
* Modify the configmap and redeploy the hub to pick up the changes.
* BERDL_NOTEBOOK_IMAGE_TAG = set to the tag of the BERDL compatible notebook image you want to use, such as `berdl-notebook:latest`

### [hub.yaml](hub.yaml)
* Modify the image tag to the tag of the BERDL JupyterHub image you want to use, you can build it locally or open a PR, and use the ghcr.io created images or a locally built image.

### [ingress.yaml](ingress.yaml)
* Ensure your hosts file matches the ingress host:
```
127.0.0.1 cdmhub.ci.kbase.us
127.0.0.1 hub.berdl.kbase.us
```
* You can get a copy of the TLS cert from our rancher if you want, otherwise you will have to use chrome and type 'thisisunsafe'
* This TLS cert should not be distributed outside of your local environment.
* If you don't want to set this up, you can change the authenticator to use `DummyAuthenticator` or similar and use `kubectl port-forward` to access the hub at `http://localhost:8000`.