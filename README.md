# 🚀 DevOps Kubernetes Assignment – Flask + MongoDB on Minikube

**Author:** Khyati Gupta

---

# 📌 Part 0 — Project Structure

```
khyatig0206-kubernetes-assignment/
│
├── app.py
├── Dockerfile
├── requirements.txt
│
└── k8s/
    ├── flask-deployment.yaml
    ├── flask-hpa.yaml
    ├── flask-service.yaml
    ├── mongodb-pv.yaml
    ├── mongodb-pvc.yaml
    ├── mongodb-secret.yaml
    ├── mongodb-service.yaml
    └── mongodb-statefulset.yaml
```

---

# 📌 Part 1 — Local Setup

### ✔ Prerequisites Installed

* Python 3.8+
* Docker Desktop
* Pip
* (Optional) Postman or curl
* kubectl (Kubernetes CLI) (Download using curl : curl.exe -LO "https://dl.k8s.io/release/v1.34.0/bin/windows/amd64/kubectl.exe")
* Minikube (Local Kubernetes Cluster) (Download from https://minikube.sigs.k8s.io/docs/start/)

---

### ✔ Create & Activate Virtual Environment

```bash
python -m venv venv
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

### ⭐ Why Virtual Environment?

Using a virtual environment:

* prevents version conflicts
* keeps dependencies isolated
* avoids breaking system Python
* ensures reproducible environment
* makes deployment easier

---

### ✔ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### ✔ Run MongoDB Locally via Docker

```bash
docker pull mongo:latest
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

MongoDB now runs on:
`mongodb://localhost:27017`

---

### ✔ Run Flask Locally

```bash
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
```

Visit:
📍 `http://localhost:5000`

---

# 📌 Part 2 — Dockerizing the Flask App

### ✔ Dockerfile Used

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

---

### ✔ Build Docker Image

```bash
docker build -t flask-mongo-app:v1 .
```

---

# 📌 Part 3 — Deploying on Minikube Kubernetes Cluster

## 3.1 Start Minikube

```bash
minikube start
```

---

## 3.2 Load Images Into Minikube

Minikube’s internal Docker daemon cannot pull from Docker Hub (due to TLS/proxy errors), so we push images manually.

### ✔ Load Flask Image

```bash
minikube image load flask-mongo-app:v1
```

### ✔ Load MongoDB Image

```bash
docker pull mongo:latest
minikube image load mongo:latest
```

---

# 📌 Part 4 — Apply Kubernetes Resources

All manifests are located in the `k8s/` directory.

---

## 4.1 Apply Kubernetes Secrets (MongoDB Credentials)

```bash
kubectl apply -f k8s/mongodb-secret.yaml
```

This creates:

```
username = admin
password = password
```

Base64 encoded in secret.

---

## 4.2 Create Persistent Volume + PVC

```bash
kubectl apply -f k8s/mongodb-pv.yaml
kubectl apply -f k8s/mongodb-pvc.yaml
```

Verifying:

```bash
kubectl get pv
kubectl get pvc
```

---

## 4.3 Deploy MongoDB StatefulSet

```bash
kubectl apply -f k8s/mongodb-statefulset.yaml
kubectl apply -f k8s/mongodb-service.yaml
```

MongoDB now runs as:

```
Pod: mongodb-0  
DNS: mongodb.default.svc.cluster.local  
Port: 27017  
```

This ensures:

* persistent storage
* stable hostname
* authentication enabled

---

## 4.4 Deploy Flask Application (2 replicas)

```bash
kubectl apply -f k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-service.yaml
```

Check pods:

```bash
kubectl get pods
```

Expected:

<img width="570" height="94" alt="image" src="https://github.com/user-attachments/assets/e316b8a2-a134-4ab5-87ad-a360611c0f1b" />

---

# 📌 Part 5 — Accessing the Application

### Step 1: Get Service URL

```bash
minikube service flask-service --url
```

Example output:

```
http://127.0.0.1:<port>
```
<img width="697" height="61" alt="image" src="https://github.com/user-attachments/assets/e8935410-54dd-45b6-b2a0-da756471b68f" />



### Step 2: Test Endpoints

#### ✔ Root endpoint

```
GET /
http://127.0.0.1:<port>/
```

Returns:

<img width="837" height="307" alt="image" src="https://github.com/user-attachments/assets/1d677b86-912b-4eb0-88e6-2eb18cd82d04" />


#### ✔ Insert data

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"name":"Khyati Gupta"}' \
http://127.0.0.1:<port>/data
```
<img width="805" height="458" alt="image" src="https://github.com/user-attachments/assets/2897d7e9-3e6d-4760-83b6-9b51953d6156" />

#### ✔ Get data

```bash
curl --location 'http://127.0.0.1:<port>/data' \
--header 'Content-Type: application/json'
```
<img width="803" height="516" alt="image" src="https://github.com/user-attachments/assets/ab3d0ebf-6ac7-46a7-877f-397035d01ecf" />

---

# 📌 Part 6 — Horizontal Pod Autoscaler (HPA)

### 6.1 Enable Metrics Server

```bash
minikube addons enable metrics-server
```

### 6.2 Apply HPA

```bash
kubectl apply -f k8s/flask-hpa.yaml
```

### 6.3 Check HPA

```bash
kubectl get hpa -w
```

---

# 📌 Part 7 — Load Testing (Cookie Point)

To test the Horizontal Pod Autoscaler (HPA), we created a special CPU-intensive route:

```python
@app.route('/load')
def load():
    x = 0
    for i in range(1000_000_000):  # more iterations → more CPU
        x += i
    return str(x)
```

This loop intentionally consumes CPU so that HPA can detect high utilization.

---

## ✔ Challenge: HPA Was Not Scaling Initially

During testing, even after sending 20–30 concurrent requests, HPA was **not scaling**.
Reasons:

* CPU usage was too low.
* The original `/load` endpoint had fewer iterations → not enough CPU pressure.
* HPA requires sustained CPU > 70% for multiple seconds.

### 🔧 Solution

We increased the loop to:

```
for i in range(1_000_000_000):
```

This caused:

* Higher CPU spikes
* Longer sustained load
* HPA successfully scaling pods from **2 → 3**

Thus to generate CPU load on Flask, `/load` endpoint is used:

```bash
./hey.exe -z 25s -c 20 http://127.0.0.1:<port>/load
```

Example:

<img width="774" height="315" alt="Screenshot 2025-11-26 175035" src="https://github.com/user-attachments/assets/c12d029c-d73d-4d6f-b769-d368453dbd43" />

Image shows HPA scaled the Deployment from 2 → 3 pods! when HPA saw CPU rising.
---

# 📌 Part 8 — DNS Resolution Explanation

Kubernetes provides DNS through CoreDNS.

### ✔ How Pods communicate:

MongoDB Service:

```
mongodb.default.svc.cluster.local
```

Inside Flask:

```
MONGO_HOST = "mongodb"
```

Kubernetes resolves `"mongodb"` → ClusterIP of MongoDB.

Thus:

```python
mongodb://admin:password@mongodb:27017/
```

automatically routes traffic to the MongoDB pod.

---

# 📌 Part 9 — Resource Requests and Limits

Both Flask and MongoDB pods use:

```
requests:
  cpu: 0.2
  memory: 250Mi

limits:
  cpu: 0.5
  memory: 500Mi
```

### ✔ Why this is important?

* **Requests** = guaranteed resources
* **Limits** = maximum allowed usage
* Prevents node overload
* Ensures MongoDB always gets enough RAM
* Allows safe autoscaling for Flask

---

# 📌 Part 10 — Design Choices

### ✔ 1. MongoDB as StatefulSet

Chosen because MongoDB needs:

* persistent identity
* dedicated volumes
* predictable naming (`mongodb-0`)

Alternative Deployment was rejected because it is stateless.

---

### ✔ 2. MongoDB Service = ClusterIP

DB must be internal-only as per requirement.

---

### ✔ 3. Flask Service = NodePort

Allows access from host machine for testing.

---

### ✔ 4. Local Images via `minikube image load`

Avoids Docker Hub pull failures (common on Windows + Docker driver).
Much faster for development.

---

### ✔ 5. Autoscaling through CPU Metrics

HPA triggered when CPU > 70%.

---

# 📌 Part 11 — Final Validation

| Feature                                | Status |
| -------------------------------------- | ------ |
| Flask runs in Kubernetes               | ✅      |
| MongoDB in StatefulSet with auth       | ✅      |
| PV + PVC for MongoDB                   | ✅      |
| Services for Flask + MongoDB           | ✅      |
| HPA scaling from 2 → 3 pods under load | ✅      |
| DNS within cluster works               | ✅      |
| Resource limits configured             | ✅      |
| All YAML files complete                | ✅      |

---
