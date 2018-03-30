# BioSimSpace Website + Notebook Installation

This directory contains all of the files needed to set up and configure
the BioSimSpace website and jupyter notebooks (including building all
custom docker images)

## Setting up the initial kubernetes cluster

This is all build in Azure

Create the cluster

```
$ az group create --name biosimspace --location westeurope
$ az aks create --resource-group biosimspace --name biosimspace --node-count 6 --generate-ssh-keys --node-vm-size Standard_A4_v2
$ az aks get-credentials --resource-group biosimspace --name biosimspace
$ kubectl get nodes
```

Creates a cluster called 'biosimspace' in the 'biosimspace' workgroup,
and then makes sure that I can connect using kubectl

This sets up six A4v2 nodes. Each node has 4 cores, 8 GB RAM and 40 GB disk.
These cost $0.18 per hour, so $26.35 per day, $790.56 per month and $9618.48
per year.

Next, creating a public static IP address...

```
$ az network public-ip create -g MC_biosimspace_biosimspace_westeurope -n static_ip --dns-name biosimspace --allocation-method Static
$  az network public-ip show -g MC_biosimspace_biosimspace_westeurope -n static_ip --query "{ address: ipAddress }"
{
  "address": "52.232.23.14"
}
```

I then setup up the router, website, notebook and workshops are detailed
in the subdirectories below.

