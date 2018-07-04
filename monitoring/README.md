# Adding in server monitoring

Have to turn off rbac on Azure using the config in values.yml

```
rbac:
  create: false
```

Then install using

```
$ helm install --name monitor --namespace monitor stable/prometheus -f prometheus.yml
$ helm install --name grafana --namespace monitor stable/grafana -f grafana.yml 
NOTES:
1. Get your 'admin' user password by running:

   kubectl get secret --namespace monitor grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

2. The Grafana server can be accessed via port 80 on the following DNS name from within your cluster:

   grafana.monitor.svc.cluster.local

   Get the Grafana URL to visit by running these commands in the same shell:

     export POD_NAME=$(kubectl get pods --namespace monitor -l "app=grafana,component=" -o jsonpath="{.items[0].metadata.name}")
     kubectl --namespace monitor port-forward $POD_NAME 3000

3. Login with the password from step 1 and the username: admin
#################################################################################
######   WARNING: Persistence is disabled!!! You will lose your data when   #####
######            the Grafana pod is terminated.                            #####
#################################################################################
```

