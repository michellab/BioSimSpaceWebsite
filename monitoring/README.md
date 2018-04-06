# Adding in server monitoring

Have to turn off rbac on Azure using the config in values.yml

```
rbac:
  create: false
```

Then install using

```
helm install --name monitor --namespace monitor stable/prometheus -f values.yml
```

