
Create the cluster

```
$ az group create --name biosimspace --location westeurope
$ az aks create --resource-group biosimspace --name biosimspace --node-count 2 --generate-ssh-keys --node-vm-size Standard_A2_v2
$ az aks get-credentials --resource-group biosimspace --name biosimspace
$ kubectl get nodes
```

Creates a cluster called 'biosimspace' in the 'biosimspace' workgroup,
and then makes sure that I can connect using kubectl

Next, creating a public static IP address...

```
$ az network public-ip create -g MC_biosimspace_biosimspace_westeurope -n static_ip --dns-name biosimspace --allocation-method Static
$  az network public-ip show -g MC_biosimspace_biosimspace_westeurope -n static_ip --query "{ address: ipAddress }"
{
  "address": "52.232.23.14"
}
```

Now creating the LoadBalancer service file to use 

```
apiVersion: v1
kind: Service
metadata:
  name: master-service
spec:
  loadBalancerIP: 52.232.23.14
  type: LoadBalancer
  ports:
  - port: 80
  selector:
    app: master-front
```

with the master-front service just being simple nginx for now...

```
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: master-front
spec:
  replicas: 1
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: master-front
    spec:
      containers:
      - name: master-front
        image: nginx:1.7.9
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 250m
          limits:
            cpu: 500m
```

Now deploy the service using

```
$ kubectl apply -f .
```

Then wait to see when everything has been connected...

```
$  kubectl get services --watch
NAME             TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
kubernetes       ClusterIP      10.0.0.1      <none>        443/TCP        3m
master-service   LoadBalancer   10.0.44.195   <pending>     80:30591/TCP   6s
master-service   LoadBalancer   10.0.44.195   52.232.23.14   80:30591/TCP   2m
```

I am now able to browse the website at http://biosimspace.westeurope.cloudapp.azure.com

# Install kubernetes from helm

This bit used the Azure Command Shell as this has helm already installed.

When I connect to Azure cloud shell, I first have to specify the 
kubernetes cluster I am working with

```
$ az aks get-credentials --resource-group biosimspace --name biosimspace
```

Next, I have to connect helm to this cluster, using

```
$ helm init
```

# Configuring Jupyter

Created a config file called "config.yaml"

Generated random seed using `openssl rand -hex 32`

```
proxy:
  secretToken: "<OUTPUT-OF-`openssl rand -hex 32`>"
rbac:
   enabled: false
```

(rbac needed as using azure aks)

Copied this across to azure cloud shell and then typed (there)

```
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
```

Then installed using

```
helm install jupyterhub/jupyterhub \
    --version=v0.6 \
    --name=jupyterhub \
    --namespace=jupyterhub \
    -f config.yaml
```

This worked, despite outputting an error. I can list the services and pods using

```
kubectl --namespace=jupyterhub get pods
kubectl --namespace=jupyterhub get services

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

This worked and I was able to start a jupyter session :-)

# Securing the platform

First I want to only allow a whitelist of users in

```
proxy:
   secretToken: "45195196f55c3611b0fbf80bb7f5eeec618d82a2edfe5dca21eb6699bfd9d779"
rbac:
   enabled: false
auth:
  whitelist:
    users:
      - chris
```

(copied to cloud shell, then)

```
helm upgrade jupyterhub jupyterhub/jupyterhub --version=v0.6 -f config.yaml
```

Getting the IP address of the server...

```
$ kubectl --namespace=jupyterhub get svc proxy-public
NAME           TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)                      AGE
proxy-public   LoadBalancer   10.0.37.112   52.233.136.58   80:32562/TCP,443:32525/TCP   9h
```

# Custom image

Ok - I have now made a custom image that uses Sire and has ambertools and
biosimspace installed. Time to upload this image to Azure...

## Azure container registry

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
$ az acr list --resource-group biosimspace --query "[].{acrLoginServer:loginServer}" --output table
AcrLoginServer
----------------
biosimspace.azurecr.io
```

I need to tag my image with the loginServer name. I also need to add ':bss-v1' to 
give a version number.

```
$ docker tag jupyter-bss biosimspace.azurecr.io/jupyter-bss:bss-v1
$ docker images
REPOSITORY                          TAG                 IMAGE ID            CREATED             SIZE
biosimspace.azurecr.io/jupyter-bss   bss-v1              381581e4f252        14 minutes ago      9.26GB
```

Next, I need to push this image to my acr using

```
$ docker push biosimspace.azurecr.io/jupyter-bss:bss-v1
$ az acr repository list --name biosimspace --output table
Result
---------------
jupyter-bss
```

I can also check the tags, using

```
$ az acr repository show-tags --name biosimspace --repository jupyter-bss --output table
Result
-----------
bss-v1
```

# Installing all

I managed to get the BioSimSpace jupyter image working by using another image
to compile amber and place this into an amber.tar.bz2 file. I also unpacked
Sire and tarred up into sire.run (really tmp_sire.app tarred up). This is because
sire.run would not install in docker because of the lack of a tty.

With these created and copied into the docker biosimspace directory, I was
able to build an image using the following docker file

```
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Ubuntu 16.04 (xenial) from 2017-07-23
# https://github.com/docker-library/official-images/commit/0ea9b38b835ffb656c497783321632ec7f87b60c
FROM ubuntu@sha256:84c334414e2bfdcae99509a6add166bbb4fa4041dc3fa6af08046a66fed3005f

LABEL maintainer="Jupyter Project <jupyter@googlegroups.com>"

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    locales \
    fonts-liberation \
    libgfortran3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Install Tini
RUN wget --quiet https://github.com/krallin/tini/releases/download/v0.10.0/tini && \
    echo "1361527f39190a7338a0b434bd8c88ff7233ce7b9a4876f3315c22fce7eca1b0 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

# Configure environment
ENV CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    AMBERHOME=/home/amber/amber16 \
    NB_USER=jovyan \
    NB_UID=1000 \
    NB_GID=100 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8
ENV PATH=$CONDA_DIR/bin:$AMBERHOME/bin:$PATH \
    HOME=/home/$NB_USER

ADD fix-permissions /usr/local/bin/fix-permissions

# Create jovyan user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    fix-permissions $HOME

ADD sire.run /tmp

# Install sire to CONDA_DIR
RUN ls -l /tmp && \
    cd /tmp && \
    echo "$CONDA_DIR" | /bin/sh ./tmp_sire.app/pkgs/sire-*/share/Sire/build/install_sire.sh && \
    ls -l /tmp && \
    ls -l $CONDA_DIR

# Change ownership of these files to jovyan user
RUN chown -R $NB_USER:$NB_GID $CONDA_DIR && \
    fix-permissions $CONDA_DIR && \
    ls -l $CONDA_DIR

USER $NB_USER

# Setup work directory for backward-compatibility
RUN mkdir /home/$NB_USER/work && \
    fix-permissions /home/$NB_USER

RUN ls -l $CONDA_DIR
RUN ls -l /tmp

# Configure the notebook and conda as jovyon
RUN $CONDA_DIR/bin/conda config --system --prepend channels conda-forge
RUN $CONDA_DIR/bin/conda config --system --set auto_update_conda false
RUN $CONDA_DIR/bin/conda config --system --set show_channel_urls true
RUN conda clean -tipsy && \
    fix-permissions $CONDA_DIR

# Install Jupyter Notebook and Hub
RUN conda install --quiet --yes \
    'notebook=5.2.*' \
    'jupyterhub=0.8.*' \
    'jupyterlab=0.31.*'

RUN pip install --upgrade pip
RUN pip install pygtail
RUN pip install matplotlib
RUN conda install watchdog

# Now clean up after conda
RUN conda clean -tipsy && \
    jupyter labextension install @jupyterlab/hub-extension@^0.8.0 && \
    npm cache clean && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    fix-permissions $CONDA_DIR

RUN pip --no-cache-dir install nglview
RUN jupyter-nbextension enable nglview --py --sys-prefix

USER root

EXPOSE 8888
WORKDIR $HOME

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]

# Add local files as late as possible to avoid cache busting
COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /etc/jupyter/
RUN fix-permissions /etc/jupyter/

# Add biosimspace files
ADD biosimspace.tar.bz2 /home/
RUN chown -R $NB_USER:$NB_GID /home/biosimspace

# Switch back to jovyan to avoid accidental container runs as root
USER $NB_USER

# install biosimspace
RUN cd /home/biosimspace/python && \
    python setup.py install

RUN /home/biosimspace/demo/nglview_patch.sh /opt/conda

# install ambertools into /home/amber
ADD amber.tar.bz2 /home/amber
```

I built this image using

```
$ docker build -t jupyter-bss .
```

Once built (which takes a long time!) I tagged this using

```
$ docker tag jupyter-bss biosimspace.azurecr.io/jupyter-bss:bss-v2
```

(this was version 2 as I made a mistake the first time)

I then pushed this to Azure into the contaner service I created using

```
$ az acr login --name biosimspace
$ docker push biosimspace.azurecr.io/jupyter-bss:bss-v2
```

I then updated the `config.yaml` that controls the helm installations
of jupyter to use this image and have th following config

```
hub:
  service:
    loadBalancerIP: 52.232.23.14
proxy:
  secretToken: "45195196f55c3611b0fbf80bb7f5eeec618d82a2edfe5dca21eb6699bfd9d779"
rbac:
  enabled: false
singleuser:
  image:
    name: biosimspace.azurecr.io/jupyter-bss
    tag: bss-v2
  storage:
    type: none
cull:
  timeout: 7200
  every: 600
auth:
  admin:
    users:
      - chris
  whitelist:
    users:
      - chris
      - lester
      - toni
      - charlie
      - adrian
      - julien
```

I then used helm to install this into the jupyterhub namespace

```
$ helm install jupyterhub/jupyterhub     --version=v0.6     --name=jupyterhub     --namespace=jupyterhub     -f config.yaml
```

I can upgrade the service when I change any of the config using

```
$ helm upgrade jupyterhub jupyterhub/jupyterhub --version=v0.6 -f config.yaml
```

To delete the service I use

```
$ helm delete jupyterhub --purge
$ kubectl delete namespace jupyterhub
```

(the above takes some time, so you have to wait until it has finished)

# Securing kubernetes

Deleting the kubernetes dashboard ad I don't use it...

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
$ kubectl --namespace jupyterhub patch svc proxy-public --type='json' -p '[{"op":"remove","path":"/spec/ports/0/nodePort"},{"op":"remove","path":"/spec/ports/1/nodePort"},{"op":"replace","path":"/spec/type","value":"ClusterIP"}]'
```

(this was based on [the instructions here](https://docs.bitnami.com/kubernetes/how-to/secure-kubernetes-services-with-ingress-tls-letsencrypt/))

# Creating a test jupyterhub

I repeated the above using a `test_config.yaml` to create a testing jupyterhub
service in the namespace "testhub". This was also patched to be a ClusterIP

# Building the ingress

Next, I created a proxy service in the main namespace using the following
service (in the `router` directory)

```
kind: Service
apiVersion: v1
metadata:
  name: notebook
spec:
  type: ExternalName
  externalName: proxy-public.jupyterhub.svc.cluster.local
  ports:
  - port: 80
---
kind: Service
apiVersion: v1
metadata:
  name: devnotebook
spec:
  type: ExternalName
  externalName: proxy-public.testhub.svc.cluster.local
  ports:
  - port: 80
```

Applying this (`kubectl apply -f notebook.yaml`) created the routing 
services. These were connected to the ingress as descirbed in the 
router directory...

All of this then worked, over HTTPS :-)

