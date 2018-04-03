# BioSimSpace Website + Notebook Installation

This directory contains all of the files needed to set up and configure
the BioSimSpace website and jupyter notebooks (including building all
custom docker images)

## Setting up the initial kubernetes cluster

This is all build in Azure

Create the cluster

```
$ az group create --name biosimspace --location eastus
$ az aks create --resource-group biosimspace --name biosimspace --node-count 6 --generate-ssh-keys --node-vm-size Standard_D4_v3
$ az aks get-credentials --resource-group biosimspace --name biosimspace
$ kubectl get nodes
```

Creates a cluster called 'biosimspace' in the 'biosimspace' workgroup,
and then makes sure that I can connect using kubectl

This sets up six D4v3 nodes. Each node has 4 fast cores, 16 GB RAM and 100 GB disk.
These cost $0.24 per node hour, so $34.56 per day, $1036.80 per month and $12614.40
per year. There is the option for reserving these for 3 years. This would bring
the cost down to $0.106 per node hour, so $15.26 per day, $457.90 per month or
$5571.36 per year.

Next, creating a public static IP address...

```
$ az network public-ip create -g MC_biosimspace_biosimspace_eastus -n static_ip --dns-name biosimspace --allocation-method Static
$ az network public-ip show -g MC_biosimspace_biosimspace_eastus -n static_ip --query "{ address: ipAddress }"
{
  "address": "52.168.53.185"
}
```

I then setup up the router, website, notebook and workshops are detailed
in the subdirectories below.

