#!/bin/bash

# Clean up any existing Kind clusters
kind get clusters && kind delete cluster --name kind || echo "No existing Kind cluster found"

# Create a new Kind cluster
kind create cluster
sleep 5  # Give it time to initialize

# Set up kubectl for the Kind cluster
export KUBEVERSION=$(kind version --client)
echo "Kube version: $KUBEVERSION"
kind get kubeconfig > kubeconfig.yaml
export KUBECONFIG=kubeconfig.yaml
kubectl cluster-info  # Verify the cluster is up

# Validate YAML manifests with kubeval (skip unknown schemas)
echo "Validating YAML files with kubeval..."
./kubeval production/full2.yaml production/secret.yaml --ignore-missing-schemas

# Apply Traefik CRDs first
echo "Applying Traefik CRDs..."
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.9/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml

# Create namespace and apply manifests
echo "Applying Kubernetes manifests..."
kubectl create namespace losstracker
kubectl apply -f production/full2.yaml --validate=false
kubectl apply -f production/secret.yaml --validate=false
kubectl apply -f production/traefik-roles.yaml --validate=false
kubectl apply -f production/default-service-account.yaml --validate=false

# Wait for deployments to become ready with proper timeout and error handling
echo "Waiting for deployments to become ready..."
if ! kubectl rollout status deployment/traefik -n losstracker --timeout=220s; then
  echo "ERROR: Traefik deployment failed to roll out"
  kubectl get pods -n losstracker
  kubectl describe deployment/traefik -n losstracker
  exit 1
fi

if ! kubectl rollout status deployment/loss-tracker-nginx-client -n losstracker --timeout=220s; then
  echo "ERROR: Client deployment failed to roll out"
  kubectl get pods -n losstracker
  kubectl describe deployment/loss-tracker-nginx-client -n losstracker
  exit 1
fi

# Test Client Ingress connectivity
echo "Port-forwarding client service to localhost:8080"
kubectl port-forward svc/loss-tracker-nginx-client 8080:80 -n losstracker &
PF_PID=$!
sleep 10
echo "Checking client service response..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
echo "HTTP status code: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "Client connectivity test failed"
  kill $PF_PID
  exit 1
fi
kill $PF_PID
echo "Client connectivity test passed"

# Test API Ingress connectivity (if available)
echo "Checking for load-balancer-server service..."
if kubectl get svc load-balancer-server -n losstracker --ignore-not-found | grep -q load-balancer-server; then
  echo "Service found, waiting for pod to be in Running state..."
  kubectl wait --for=condition=ready pod -l app=loss-tracker-server -n losstracker --timeout=120s
  echo "Port-forwarding API service to localhost:5005"
  kubectl port-forward svc/load-balancer-server 5005:5005 -n losstracker &
  PF_API_PID=$!
  sleep 10
  echo "Checking API endpoint response..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5005/)
  echo "HTTP status code: $HTTP_CODE"
  if [ "$HTTP_CODE" != "200" ]; then
    echo "API connectivity test failed"
    kill $PF_API_PID
    exit 1
  fi
  kill $PF_API_PID
  echo "API connectivity test passed"
else
  echo "Service load-balancer-server not found; skipping API connectivity test"
fi

# Test Traefik routing for /api path - Fixed version
echo "Testing Traefik routing for /api path"
INGRESS_EXISTS=$(kubectl get ingress -n losstracker --ignore-not-found -o jsonpath='{.items[0].metadata.name}')
echo "Ingress exists: $INGRESS_EXISTS"
if [ -n "$INGRESS_EXISTS" ]; then
  echo "Ingress found: $INGRESS_EXISTS. Proceeding to check routing for /api"

  # Port-forward the Traefik service to make it accessible locally
  echo "Port-forwarding Traefik service to localhost:8000"
  kubectl port-forward svc/traefik 8000:80 -n losstracker &
  TRAEFIK_PF_PID=$!
  sleep 5

  # Test the routing for /api with host header
  echo "Testing API endpoint through Traefik..."
  RESPONSE=$(curl -s -D - -o /dev/null -H "Host: mlstatstracker.org" http://localhost:8000/api/)
  HTTP_CODE=$(echo "$RESPONSE" | grep HTTP | awk '{print $2}')
  echo "HTTP status code received for /api: $HTTP_CODE"
  
  # Clean up port-forward
  kill $TRAEFIK_PF_PID
  
  # Check response code
  if [[ "$HTTP_CODE" =~ ^(200|302|307|308)$ ]]; then
    echo "Traefik routing for /api path passed successfully with HTTP status $HTTP_CODE"
  else
    echo "ERROR: Traefik routing for /api path failed. Received HTTP code: $HTTP_CODE"
    # Print diagnostic information
    echo "Checking Traefik logs..."
    kubectl logs -l app.kubernetes.io/name=traefik -n losstracker --tail=50
    echo "Checking ingress configuration..."
    kubectl get ingress -n losstracker -o yaml
    exit 1
  fi
else
  echo "Ingress not found in namespace 'losstracker'; skipping /api path routing test"
fi

echo "All tests completed successfully!"

