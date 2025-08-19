# Info
* Deploy k8 resources into your local cluster, such as rancher2 desktop
* These were adapted from https://gitlab.kbase.lbl.gov/berdl/configmaps and https://gitlab.kbase.lbl.gov/berdl/manifests using  `kustomize build . | pbcopy` within the directory to copy the k8 resources 

# Deployment
Use the provided local_dev directory to deploy the JupyterHub instance. This directory contains all necessary Kubernetes manifests and configurations.


# [configmap.yaml](configmap.yaml)
* Modify the configmap and redeploy the hub to pick up the changes.
* BERDL_NOTEBOOK_IMAGE_TAG = set to the tag of the BERDL compatible notebook image you want to use, such as `berdl-notebook:latest`

# [hub.yaml](hub.yaml)
* Modify the image tag to the tag of the BERDL JupyterHub image you want to use, you can build it locally or open a PR, and use the ghcr.io created images or a locally built image.


# [ingress.yaml](hub.yaml)
* Ensure your hosts file matches the ingress host such as
```aiignore
127.0.0.1 cdmhub.ci.kbase.us
127.0.0.1 hub.berdl.kbase.us
```
* you can get a copy of the TLS cert from our rancher if you want, otherwise you will have to use chrome and type 'thisisunsafe'
