#### is able to show real time data with the optim python API and to acces data from the DB ####
`use test`
`db.training_eval.distinct('name')`
<img width="726" alt="Screen Shot 2022-04-01 at 9 59 41 PM" src="https://user-images.githubusercontent.com/63979635/161333230-d9d157dc-bb47-4c8d-9b98-62b140464a2e.png">

To build the docker image for production run:
eval $(minikube docker-env)
//docker compose -f docker-compose.build.yml up
docker build -t loss-tracker-server .
This command builds the image and then runs the image in a container.
Stop the container and run minikube start
Switch namespace to losstracker by running: kubens losstracker
if the namespace doesn't exist yet run: kubectl create namespace losstracker

To run the deployment run:
kubectl apply -f deployment.yaml

Client:
eval $(minikube docker-env) (for imagePullPolicy: Never the images need to be on the minikube node)
run docker build -t loss-tracker-client .

kubectl apply -f deployment.yaml

Deploy with Ingress: 
kubectl apply -f ingress.yaml
after changing the domain the server is still only reachable via localhost or 127.0.0.0
