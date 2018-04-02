
# Install kubernetes from helm

This bit used the Azure Command Shell as this has helm already installed.

When I connect to Azure cloud shell, I first have to specify the 
kubernetes cluster I am working with

```
$ az aks get-credentials --resource-group biosimspace --name biosimspace
```

## Azure container registry

I had to create custom images for the notebook. [See here](../docker)

Now need to create an Azure container registry to store my custom image. I will
do this in the `biosimspace` resource group that contains the aks cluster.

```
$ az acr create --resource-group biosimspace --name biosimspace --sku Basic
```

Next I have to login to this acr instance...

```
$ az acr login --name biosimspace
```

Next I need to get the login server name for my acr

```
$ az acr list --resource-group biosimspace --query "[].{acrLoginServer:loginServer}" --ou$
AcrLoginServer
----------------
biosimspace.azurecr.io
```

I need to tag my image with the loginServer name. I also need to add ':bss-v1' to
give a version number.

```
$ docker tag biosimspace biosimspace.azurecr.io/biosimspace:v1
$ docker images
REPOSITORY                          TAG                 IMAGE ID            CREATED	 $
biosimspace.azurecr.io/biosimspace  v1                  381581e4f252        14 minutes a$
```

Next, I need to push this image to my acr using

```
$ docker push biosimspace.azurecr.io/biosimspace:v1
$ az acr repository list --name biosimspace --output table
Result
---------------
biosimspace
```

I can also check the tags, using

```
$ az acr repository show-tags --name biosimspace --repository biosimspace --output table
Result
-----------
v1
```

# Helm installation

Next, I have to connect helm to the kubernetes cluster, using

```
$ helm init
```

# Allowing kubernetes to connect to acr

Must give permission to the pods to access the acr

```
$ CLIENT_ID=$(az aks show --resource-group biosimspace --name biosimspace --query "servicePrincipalProfile.clientId" --output tsv)
$ ACR_ID=$(az acr show --name biosimspace --resource-group biosimspace --query "id" --output tsv)
$ az role assignment create --assignee $CLIENT_ID --role Reader --scope $ACR_ID
```

# Configuring Jupyter

Created a config file called [notebook.yaml](notebook.yaml)

(rbac needed as using azure aks)

Then ensured that helm could download jupyterhub

```
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
```

Then installed using

```
helm install jupyterhub/jupyterhub --version=v0.6 --timeout=36000 --debug --name=notebook --namespace=notebook -f notebook.yaml
```

I use a large timeout and debug as pulling the images takes a long time
(particularly the custom jupyterhub image I use)

```
kubectl --namespace=notebook get pods
kubectl --namespace=notebook get services

NAME                     READY     STATUS     RESTARTS   AGE
hub-3057663432-c0rz2     1/1       Running    0          8m
jupyter-test             0/1       Init:0/1   0          3m
proxy-2160975612-kjcnf   2/2       Running    0          8m

NAME           TYPE           CLUSTER-IP     EXTERNAL-IP     PORT(S)                      AGE
hub            ClusterIP      10.0.118.30    <none>          8081/TCP                     8m
proxy-api      ClusterIP      10.0.5.177     <none>          8001/TCP                     8m
proxy-http     ClusterIP      10.0.158.110   <none>          8000/TCP                     8m
proxy-public   LoadBalancer   10.0.37.112    52.233.136.58   80:32562/TCP,443:32525/TCP   8m
```

# Upgrading and deleting

I can upgrade the service when I change any of the config using

```
$ helm upgrade notebook jupyterhub/jupyterhub --timeout=36000 --debug --version=v0.6 -f notebook.yaml
```

To delete the service I use

```
$ helm delete notebook --purge
$ kubectl delete namespace notebook
```

(the above takes some time, so you have to wait until it has finished)

# Securing kubernetes

Deleting the kubernetes dashboard as I don't use it...

```
$ kubectl --namespace=kube-system delete deployment kubernetes-dashboard
```

Limiting public access to the Tiller API

```
$ kubectl --namespace=kube-system patch deployment tiller-deploy --type=json --patch='[{"op": "add", "path": "/spec/template/spec/containers/0/command", "value": ["/tiller", "--listen=localhost:44134"]}]'
```

# Now switching the LoadBalance to ClusterIP

As I am using my own ingress, I need to turn the LoadBalancer on service
proxy-public into a ClusterIP

```
$ kubectl --namespace notebook patch svc proxy-public --type='json' -p '[{"op":"remove","path":"/spec/ports/0/nodePort"},{"op":"remove","path":"/spec/ports/1/nodePort"},{"op":"replace","path":"/spec/type","value":"ClusterIP"}]'
```

(this was based on [the instructions here](https://docs.bitnami.com/kubernetes/how-to/secure-kubernetes-services-with-ingress-tls-letsencrypt/))

# Creating notebookdev and workshop

I repeated the above to create a notebookdev (for testing) and workshop (for workshops)
jupyterhubs. These were configured using;

* [workshop.yaml](workshop.yaml) : `--name=workshop --namespace=workshop -f workshop.yaml`
* [notebookdev.yaml](notebookdev.yaml) : `--name=notebookdev --namespace=notebookdev -f notebookdev.yaml`

# Building the ingress

Next, I created a proxy service in the main namespace using the following
service (as described in [router](../router))

```
kind: Service
apiVersion: v1
metadata:
  name: notebook
spec:
  type: ExternalName
  externalName: proxy-public.notebook.svc.cluster.local
  ports:
  - port: 80
---
kind: Service
apiVersion: v1
metadata:
  name: notebookdev
spec:
  type: ExternalName
  externalName: proxy-public.notebookdev.svc.cluster.local
  ports:
  - port: 80
---
kind: Service
apiVersion: v1
metadata:
  name: workshop
spec:
  type: ExternalName
  externalName: proxy-public.workshop.svc.cluster.local
  ports:
  - port: 80
```

Applying this (`kubectl apply -f notebook.yaml`) created the routing 
services. These were connected to the ingress as descirbed in the 
router directory...

All of this then worked, over HTTPS :-)
