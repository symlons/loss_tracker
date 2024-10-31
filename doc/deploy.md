# Kubernetes Deployment Guide

This guide explains how to deploy the application to a Kubernetes cluster after initial setup.

## Prerequisites

- A configured Kubernetes cluster
- `kubectl` CLI tool installed
- Access to necessary Docker images

## Deployment Steps

### 1. Configure Secrets and ConfigMap

First, navigate to the server production directory and apply the necessary configurations:

```bash
cd loss_tracker/server/production

# Apply secrets for Docker image pulling
kubectl apply -f secret.yaml

# Apply server configuration
kubectl apply -f server-configmap.yaml
```

### 2. Deploy Server Components

While in the server production directory, deploy the server components:

```bash
# Apply server deployment
kubectl apply -f deployment.yaml

# Apply server service
kubectl apply -f service.yaml
```

### 3. Deploy Client Components

Navigate to the client production directory and deploy the Nginx components:

```bash
cd ../../client/production

# Apply Nginx deployment
kubectl apply -f nginx-deployment.yaml

# Apply Nginx service
kubectl apply -f nginx-service.yaml
```

### 4. Configure Ingress

Return to the server production directory and set up the Traefik ingress:

```bash
cd ../../server/production

# Apply Traefik ingress configuration
kubectl apply -f traefik_ingress.yaml
```

### 5. Configure DNS

Map the ingress IP address to the hostname in the local hosts file:

```bash
# Edit hosts file
sudo vim /etc/hosts

# Add mapping
<INGRESS_IP> <HOSTNAME>
```

## Verification

After completing these steps, the application should be accessible through the configured hostname. You can verify the deployment status using:

```bash
kubectl get pods
kubectl get services
kubectl get ingress
```
