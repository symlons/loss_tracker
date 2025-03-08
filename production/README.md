kubectl patch svc traefik -n losstracker --type='json' -p='[{"op": "replace", "path": "/spec/selector", "value": {"app.kubernetes.io/name": "traefik"}}]'
