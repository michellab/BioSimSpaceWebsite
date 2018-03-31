# Built the ingress using the files here

# Setting up https

Installing kube-lego using

```
$ helm install stable/kube-lego --namespace router --set config.LEGO_EMAIL=Christopher.Woods@bristol.ac.uk,config.LEGO_URL=https://acme-v01.api.letsencrypt.org/directory
```

I then created the ingress objects using

Default backend

```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: default-http-backend
  labels:
    k8s-app: default-http-backend
  namespace: router
spec:
  replicas: 1
  template:
    metadata:
      labels:
        k8s-app: default-http-backend
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: default-http-backend
        # Any image is permissable as long as:
        # 1. It serves a 404 page at /
        # 2. It serves 200 on a /healthz endpoint
        image: gcr.io/google_containers/defaultbackend:1.4
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          timeoutSeconds: 5
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: 10m
            memory: 20Mi
          requests:
            cpu: 10m
            memory: 20Mi
---
apiVersion: v1
kind: Service
metadata:
  name: default-http-backend
  namespace: router
  labels:
    k8s-app: default-http-backend
spec:
  ports:
  - port: 80
    targetPort: 8080
  selector:
    k8s-app: default-http-backend
```

then the ingress deployment

```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: nginx-ingress-controller
  labels:
    k8s-app: nginx-ingress-controller
  namespace: router
spec:
  replicas: 1
  template:
    metadata:
      labels:
        k8s-app: nginx-ingress-controller
      annotations:
        prometheus.io/port: '10254'
        prometheus.io/scrape: 'true'
    spec:
      # hostNetwork makes it possible to use ipv6 and to preserve the source IP correctly regardless of docker configuration
      # however, it is not a hard dependency of the nginx-ingress-controller itself and it may cause issues if port 10254 already is taken on the host
      # that said, since hostPort is broken on CNI (https://github.com/kubernetes/kubernetes/issues/31307) we have to use hostNetwork where CNI is used
      # like with kubeadm
      # hostNetwork: true
      # Check latest version here: https://github.com/kubernetes/ingress-nginx/releases
      terminationGracePeriodSeconds: 60
      containers:
      - image: quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.10.2
        name: nginx-ingress-controller        
        ports:
        - containerPort: 80
          hostPort: 80
        - containerPort: 443
          hostPort: 443
        env:
          - name: POD_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
          - name: POD_NAMESPACE
            valueFrom:
              fieldRef:
                fieldPath: metadata.namespace
        args:
        - /nginx-ingress-controller
        - --default-backend-service=$(POD_NAMESPACE)/default-http-backend
```

then the ingress service that attaches to the public static IP that
I set originally in the jupyterhub script

```
apiVersion: v1
kind: Service
metadata:
  name: ingressservice
  namespace: router
spec:
  ports:
    - port: 80
      name: http
    - port: 443
      name: https
  selector:
    k8s-app: nginx-ingress-controller
  loadBalancerIP: 52.232.23.14
  type: LoadBalancer
```

and finally the router that routes different subdomaines to different
kubernetes services, and also automatically gets the LetsEncrypt 
SSL certificates.

```
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: rewrite  
  annotations:    
    kubernetes.io/ingress.class: nginx
    kubernetes.io/tls-acme: 'true'
spec:
  rules:
  - host: biosimspace.org
    http:
      paths:
      - path: /
        backend:
          serviceName: web
          servicePort: 80
  - host: www.biosimspace.org
    http:
      paths:
      - path: /
        backend:
          serviceName: web
          servicePort: 80
  - host: notebook.biosimspace.org
    http:
      paths:
      - path: /
        backend:
          serviceName: notebook
          servicePort: 80
  - host: notebookdev.biosimspace.org
    http:
      paths:
      - path: /
        backend:
          serviceName: devnotebook
          servicePort: 80
  tls:
  - secretName: web-tls-cert
    hosts:
    - biosimspace.org
    - www.biosimspace.org
    - notebook.biosimspace.org
    - wwwdev.biosimspace.org
    - notebookdev.biosimspace.org
```

I thne applied everything usng

```
$ kubectl apply -f .
```

This is now all working. I have the webserver available at
https://biosimspace.org and https://www.biosimspace.org,
the notebook at https://notebook.biosimspace.org and
the development notebook at https://nodebookdev.biosimspace.org.

# Rewriting full URLs

One issue is that the theme I am using for wordpress is forcing
some images (notably background, icon and logo) to be served from
a static http URL (http://biosimspace.org/wp-content/uploads/2018/02/logo.jpeg).

I need to add a rewrite rule that */wp-content/uploads/* should be rewritten
to https://domain/wp-content/uploads/*. How do I do this?

Still tryinh..

# Scaling pods

I have scaled the wordpress pod so that tehre are two replicas, using

```
$ kubectl --namespace wordpress scale --replicas=2 deployment web-wordpress
```

This is verfied using

```
$ kubectl --namespace wordpress get podsNAME                             READY     STATUS    RESTARTS   AGE
web-mariadb-4176818430-vb3sl     1/1       Running   0          23m
web-wordpress-1001763379-5t8hd   1/1       Running   0          23m
web-wordpress-1001763379-x8wqh   1/1       Running   0          3m
```

