
import os
import sys

pods = os.popen("kubectl --namespace workshop get pods", "r").readlines()

for pod in pods:
    name = pod.split()[0]
    if name.startswith("jupyter-"):
        cmd = "kubectl --namespace workshop delete pod %s" % name
        print(cmd)
        os.system(cmd)
