#### Loss Tracker
The Loss Tracker helps track model training and experiments.
The project consists of a Python interface which can send data to a backend. The backend streams this data to the frontend for visualization:

<img width="726" alt="Screen Shot 2022-04-01 at 9 59 41 PM" src="https://user-images.githubusercontent.com/63979635/161333230-d9d157dc-bb47-4c8d-9b98-62b140464a2e.png">

Experiments can be stored and later retrieved via the specified name in the Python logging request.

## Development Setup
### Frontend
```
cd client && npm run dev
```

### Backend
```
cd server && npx nodemon
```
Documentation about the Python interface can be found in tracker/.

### Deployment
In the Github Actions workflow the project gets build for arm64. These images can be used to deploy on a configured Kubernetes cluster.
The configuration files for the Kubernetes Ingress and Deployment can be found in server/production and client/production.





