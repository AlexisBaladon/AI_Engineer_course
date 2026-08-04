# NauAI - Coderhouse AI Engineering course
Welcome to NauAI, the (un)official AI of the chess club [Nau64](https://nau64.com). This is an agent in charge of answering questions about the chess institute Nau64. I made this project with the intentions of creating an application about a chess club I started going to in January of 2026, where I spend my free time playing tournaments.

![NAU onboarding](./docs/nau_onboarding.png)


This is an example of an experimental feature only available for admin users. The club uploads the the matches from the 4 players with the highest ranking in that tournament on a weekly basis to their website using smart chess boards, which makes the plays available for retrieval. There's also a library named `chess` which converts sequences of steps in SAN format into board images, which makes it possible with the use of AI to dynamically create board images using tools. The retriever is still not good at finding matches with specific details like finding matches with queries like "show me that plays made in board 1 and round 5 of the tournament", and some queries cause the AI to generate really long sequences of plays, delaying the response, which made me think of making this feature admin-only by now.

![Chess board feature](./docs/tool_demo.jpeg)

## 🔐 Environment Variables

Copy in an `.env` file in the root of the project and fill in the values for the following environment variables:
```
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>
LANGSMITH_PROJECT=<YOUR_LANGSMITH_PROJECT>
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
ADMIN_USER_USERNAME=<CHOOSE_AN_ADMIN_USER_USERNAME>
ADMIN_USER_PASSWORD=<CHOOSE_AN_ADMIN_USER_PASSWORD>
ENCRYPTION_SECRET_KEY=<CHOOSE_YOUR_ENCRYPTION_SECRET_KEY>
DEBUG=true
```

Description of the environment variables used in the application:
- `LANGSMITH_TRACING`: Enables tracing for LangSmith API calls.
- `LANGSMITH_ENDPOINT`: The endpoint for the LangSmith API. 
- `LANGSMITH_API_KEY`: Your API key for LangSmith.
- `LANGSMITH_PROJECT`: The project name for LangSmith.
- `OPENAI_API_KEY`: Your API key for OpenAI.
- `ADMIN_USER_USERNAME`: The username for the admin user. It could be "admin".
- `ADMIN_USER_PASSWORD`: The password for the admin user. It could be "123".
- `ENCRYPTION_SECRET_KEY`: A secret key used for encryption. It could be generate using python -c "import secrets; print(secrets.token_hex(16))".


## 💻🖥️💻 Deployment option 1: Kubernetes

### 1. Verify kubernetes cluster is created
Kubernetes must be installed and a cluster must be created in order to run the application.

```
kubectl cluster-info
```

### 2. Verify that secret (environment variables) is created.
You must create a secret file from the .env file in order to run the application. 
This scripts converts a .env file into a secret in Kubernetes.

```
kubectl create secret generic nau-secret --from-env-file=.env -n nau-ai
```

### 3. Create the namespace, deployment, and service in Kubernetes 
```
kubectl apply --recursive -f k8_deploy/
```

### 4. Ensure ports are forwarded to the local machine
Using different consoles:

```
kubectl port-forward service/frontend 5173:5173 -n nau-ai
```

```
kubectl port-forward service/hook 1235:1235 -n nau-ai
```

### 5. Verify that the configuration is correct and the pods are running
Get information from the different resources in the Kubernetes cluster.
```
kubectl get namespaces
```

```
kubectl get deployments -n nau-ai
```

```
kubectl get pods -n nau-ai
```

```
kubectl get services -n nau-ai
```


Get information from a particular pod in the Kubernetes cluster.

```
kubectl describe pod <POD_NAME> -n nau-ai
```

```
kubectl logs <POD_ID> -n nau-ai
```

### 6. If anything goes wrong
You can delete the deployment and start over by running the following command:
```
kubectl delete deployment -n nau-ai --all
```

### 7. If you change the source code of the application
In order to build and push docker images to dockerhub, which are then pulled by Kubernetes, you must be logged in to dockerhub and run the following command:
```
python push_docker_containers.py --username <DOCKERHUB_USERNAME>
```

Always make sure that the containers you push are public so that anyone can pull the images.

## 🐳 Deployment option 2: Docker compose
### 1. Build and run the docker images
```
docker compose --build up
```

## 🐍⚛️ Deployment option 3: Light version - Monolithic Python backend & React (Recommended)
### 1. Install dependencies
For the backend:
```
pip install -r requirements.txt
```

Note: This method inicializes a monolithic Python application, importing the methods of the application instead of making API calls. This is used for less expensive deployments, such as on AWS. It is also possible to run each microservice independently, but this requires more resources and is more costly:

```
cd <MICROSERVICE_FOLDER>
pip install -r requirements.txt
```

For the frontend:
```
cd frontend/my-app
npm install
```


### 2. Run the application

To run the backend in a single server:
```
python app.py
```

To run every microservice independently:
```
cd <MICROSERVICE_FOLDER>
python app.py
```

To run the frontend (requires npm):
```
cd frontend/my-app
npm run dev
```

## 💫 Deployment option 4: Netlify & AWS

### Deploying the application for the first time

**Netlify**:
- Build the frontend using `npm run build` in the `frontend/my-app` folder.
- Deploy the frontend to Netlify. You can use the `frontend/my-app/dist` folder as the source for the deployment.

**AWS**:
- Initialize an EC2 instance and install the required dependencies using `./aws_deploy/setup_project.sh`.
- Buy a domain name and create a hosted zone in Route53.
- Associate the domain name with an Elastic IP and point the Elastic IP to the EC2 instance.
- Copy the environment variables from the `.env` file to the EC2 instance.
- Setup the reverse proxy using `./aws_deploy/setup_nginx.sh`.
- Setup the HTTPS certificate using `./aws_deploy/setup_https.sh`.
- Create a virtual environment using `python3 -m venv nau_ai`. It's important to use that name for the virtual environment, as it is used in the `nauai.service` file.
- Copy the file `nauai.service` to `/etc/systemd/system/nauai.service` in the EC2 instance. Remember to use sudo to copy the file.
- Incorporate inside the header http: limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m; in the `/etc/nginx/nginx.conf` file. Remember to use sudo to edit the file.
- Start the service using `sudo systemctl daemon-reload`,  `sudo systemctl enable nauai` and `sudo systemctl start nauai`.
- Verify that the service is running using `sudo systemctl status nauai`.


### Making changes to nginx
If you want to change the configuration of the nginx.conf file, use: 

```
source nau_ai/bin/activate
pip install -r requirements.txt
sudo systemctl restart nauai
```

### Making changes to the service
If you want to change the configuration of the nauai.service file, use: 

```
sudo systemctl daemon-reload
sudo systemctl restart nauai
```


## 🌐 Deployment option 5: Access to an already deployed application
You can access the deployed application at the following URL: [https://nauai.netlify.app/](https://nauai.netlify.app/)


## 🏠 Architectural decisions
### Flow of the application
![./docs/nau_flowchart.png](./docs/nau_flowchart.png)

### Microservices architecture of the application
![./docs/nau_microservices.png](./docs/nau_microservices.png)

The components present here are:
- **Frontend**: The frontend is a React application that allows the user to interact with the application.
- **Hook**: The hook is a Flask application that receives the user question and sends it to the orchestrator, and handles user authentication and authorization. The reason for having this hook is to divide the responsabilities of the orchestrator and the authentication, and having the frontend only communicate with one application.
- **Orchestrator**: The orchestrator is a Flask application that coordinates the different components of the application. It receives the user question from the hook and sends it to the retrieval component, then sends the retrieved documents to the ranking component, and finally sends the ranked documents to the agent component. The orchestrator also handles the communication with LangSmith for observability.
- **Filter**: The filter is a Flask application that filters user queries to ensure that they are appropriate and do not contain any sensitive information. It uses the `gpt-4.1-mini` model to filter the queries.
- **Retrieval**: The retrieval component is a Flask application that retrieves documents from the vectorial database using the user question. It uses the `text-embedding-3-large` model to generate embeddings for the user question and the documents, and then uses a hybrid search method to retrieve the most relevant documents. The application also uses semantic chunking, hybrid search, and stopword cleaning to increase the performance of the retriever.
- **Ranking**: The ranking component is a Flask application that ranks the retrieved documents using the `gpt-4.1-mini` model. It receives the retrieved documents and the user question from the orchestrator, and returns the ranked documents to the orchestrator.
- **Judge**: The judge is a Flask application that evaluates whether the answer generated by the agent is faithful to the retrieved documents. It uses the `gpt-4.1-mini` model to evaluate the faithfulness of the answer. It also re-writes queries to make them more specific and relevant to the retrieved documents. Its main purpose was to have at least 1 module which used cyclical loops provided by LangGraph. As it's expensive, it can be disabled using `max_iterations=0` in the module that calls it. I don't use it in the monolithic version of this app (`/app.py`), as I don't want the official version to have that level of complexity. 
- **Agent**: The agent is a Flask application that generates an answer to the user question using the ranked documents. It uses the `gpt-4.1-mini` model to generate the answer, and it can also decide whether to retrieve more documents or not based on the ranked documents and the user question.


### Ingestion
The ingestion of documents is done using the `ingestion/ingestion.ipynb` notebook. The script uses the `text-embedding-3-large` model to generate embeddings for the documents, and then stores the embeddings in a CSV file.


### Metrics
The metrics defined for the application are:
- Latency: The time it takes for the application to respond to a request.
- Faithfulness: The percentage of answers that are faithful to the retrieved documents.
- Document precision@k: The percentage of relevant documents retrieved in the top k documents.
- Application cost: The cost of running each query. This cost can be found in LangSmith traces.

A summary of the application metrics can be found in the `evaluation/README.md` file, and inside `README.md`.


New metrics can also be generated by using the `evaluation/get_llm_outputs.py`, `evaluation/calculate_metrics.py`, `evaluation/create_report.py`, and `evaluation/update_readme.py` scripts, subsequently. The scripts will generate a new report in the `evaluation/report.md` file.


## 📝 Coderhouse project requirements

### Folders for every component:
- **retrieval/**: Contains the retrieval component.
- **ranking/**: Contains the ranking component.
- **orchestation/**: Contains the orchestration component.
- **agent/**: Contains the agent component.
- **agent/mcp_adapters/**: Contains the MCP adapters component.
- **orchestation/observability/**: Contains the observability component.

### Documentation
- See the `README.md` file to check the architecture and how to run each module.

### Components
- Retrieval:
    - ✅ Retrieval module in `retrieval/`.
    - ✅ Vectorial database: The application uses FAISS as a vectorial database.
- Ranking:
    - ✅ Ranking module in `ranking/`.
- Orchestration:
    - ✅ Orchestration module in `orchestation/`.
    - ✅ Coordination of LLMs: For example, the re-ranker and the agent are orchestrated to work together. 
    - ✅ Use of tools: The application has a tool in charge of rendering plays from chess boards, if the retriever finds moves from players.
- Agent:
    - ✅ Agent module in `agent/`.
    - ✅ Cyclic agent using LangGraph: I use a cyclic agent to decide if the retrieved documents are enough to answer the question or if it needs to retrieve more documents.
- MCP Adapters:
    - ✅ MCP adapters in `agent/mcp_adapters/`. I use adapters to prevent non-admin users from accessing my experimental image generation feature.
- Deployment:
    - ✅ Deployment scripts for Kubernetes created in `k8_deploy/`.
    - ✅ Scaling: The application can be scaled by changing the number of replicas in the deployment.yaml file.
- Observability:
    - ✅ Observability module in `orchestation/observability/`.
    - ✅ LangSmith integration: I use LangSmith to collect logs, metrics and traces.
    - ✅ Arize Phoenix integration: I use Arize to calculate metrics in `evaluation/README.md`.
    - ✅ Metrics defined: Latency, hallucination rate, Document precision@k. They can be found at `evaluation/README.md`, and you can find costs and latency using *langsmith* console too.
- Architectural decisions:
    - ✅ All architectural decisions are documented in the `README.md` file.
    - ✅ Deployment and monitoring process: Described in the `README.md` file.

<!-- BEGIN AUTO-GENERATED EVALUATION -->

# 🧠 Nau64 RAG Evaluation Report

> Automatically generated benchmark report.

---

# 📋 Experiment Information

| Property | Value |
|-----------|------:|
| Date | 2026-08-04T19:55:39.473948+00:00 |
| Git Commit | `79d0a9ea6912e5a918fc7b80c7f6dfc3f1ecb0ff` |
| Embedding Model | text-embedding-3-large |
| Retrieval Method | Hybrid Search |
| Re-ranking Model | gpt-4.1-mini |
| LLM | gpt-4.1-mini |
| Number of Questions | 100 |

---

# 📊 Overall Metrics

| Metric | Value |
|---------|------:|
| Average Time to First Token | **6.26 s** |
| Average Faithfulness | **1.000** |
| Precision@k | **0.730** |

---

# ✅ Faithfulness Distribution

| Label | Count |
|--------|------:|
    | faithful | 100 |


---

# ⚡ Latency

| Metric | Seconds |
|---------|--------:|
    | Fastest TTFT | 4.53 |
| Slowest TTFT | 22.21 |


---

# 📈 Executive Summary

This benchmark evaluated **100** user questions against the
latest version of the Nau64 RAG system.

## Highlights

- Average Time to First Token: **6.26 seconds**
- Average Faithfulness: **1.000**
- Average Precision@k: **0.730**

The benchmark was generated automatically from commit `79d0a9ea6912e5a918fc7b80c7f6dfc3f1ecb0ff` on
2026-08-04T19:55:39.473948+00:00.

<!-- END AUTO-GENERATED EVALUATION -->



