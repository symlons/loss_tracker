# Kubernetes Command Reference

## Inspecting Pods
To inspect if all pods are running, run:
```bash
kubectl get pods -A
```

## Setting a Namespace
To create a namespace:
```bash
kubectl create namespace <namespace-name>
```
Or use `kubens` if installed to quickly switch namespaces.

## Getting Logs
To get the logs of a pod, use:
```bash
kubectl logs <pod_name> -n <namespace>
```

## Describing a Pod
To get the description of a pod, such as its IP and port, run:
```bash
kubectl describe pod <pod_id> -n <namespace>
```

## Viewing Pod Events
To get the events of a pod:
```bash
kubectl get events --namespace <namespace> --field-selector involvedObject.name=<pod_name>
```

## Additional Information for a Service
To get additional information about a service, such as its IP, run:
```bash
kubectl get svc -o wide -n <namespace>
```

## Namespace Specification
The `-n` flag defines the namespace for the command.
