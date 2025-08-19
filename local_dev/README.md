# Info
* Deploy k8 resources into your local cluster, such as rancher2 desktop
* These were adapted from https://gitlab.kbase.lbl.gov/berdl/configmaps and https://gitlab.kbase.lbl.gov/berdl/manifests using  `kustomize build . | pbcopy` within the directory to copy the k8 resources 

# Deployment
* Modify the configmaps in `local_dev/configmaps` to your local environment, such as NODE_SELECTOR
* Deploy the configmaps with `kubectl apply -k local_dev/configmap.yaml` or drag/drop into the rancher2 desktop UI
* Deploy the manifests with `kubectl apply -k local_dev/berdlhub.yaml` or drag/drop into the rancher2 desktop UI

# configmap.yaml
* Modify the configmap and redeploy the hub to pick up the changes.
* BERDL_NOTEBOOK_IMAGE_TAG = set to the tag of the BERDL compatible notebook image you want to use, such as `berdl-notebook:latest`

# hub.yaml
* Modify the image tag to the tag of the BERDL JupyterHub image you want to use, you can build it locally or open a PR, and use the ghcr.io created images.

# Port Forwarding
kubectl port-forward deployment/jupyterhub 8000:8000 --namespace=jupyterhub-dev