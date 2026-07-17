# AI_Engineer_course
Source code of my Coderhouse AI Engineer course submissions

## Deployment using K8

### Verify kubernetes cluster is created
Kubernetes must be installed in order to run the application.

kubectl cluster-info

### Creating a secret in Kubernetes
You must create a secret file from the .env file in order to run the application.

kubectl create secret generic nau-secret --from-env-file=.env -n nau-ai


### Creating the namespace, deployment, and service in Kubernetes 
kubectl apply --recursive -f k8s/

### Port forwarding
kubectl port-forward service/frontend 5173:5173 -n nau-ai
kubectl port-forward service/hook 1235:1235 -n nau-ai


### Delete replicas
kubectl delete deployment -n nau-ai --all

### If something goes wrong
kubectl get namespaces
kubectl get deployments -n nau-ai
kubectl get pods -n nau-ai
kubectl get services -n nau-ai
kubectl describe pod agent-f447658f5-4cv8n -n nau-ai
kubectl logs agent-f447658f5-w8jf2 -n nau-ai
kubectl config current-context


## Deployment using Docker compose
### Build the docker images
docker compose --build up