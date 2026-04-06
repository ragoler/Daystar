from abc import ABC
from pydantic import BaseModel
import time
import subprocess
import os
import requests
from backend.probers import BaseProber, ProberResult
from backend.database import log_api_call

try:
    from google.cloud import container_v1
    from google.protobuf.json_format import MessageToDict
except ImportError:
    container_v1 = None
    MessageToDict = None

class GkeProber(BaseProber):
    def __init__(self, operation: str, project_id: str, location: str, data_dir: str = "data"):
        self.operation = operation
        self.project_id = project_id
        self.location = location
        self.data_dir = data_dir
        self.logs = ""
        self.client = None
        
        if container_v1:
            self.client = container_v1.ClusterManagerClient()
        else:
            self.logs += "Warning: google-cloud-container not installed. Real GKE operations will fail.\n"

    def execute(self, resource_name: str) -> ProberResult:
        self.logs += f"Starting GKE operation: {self.operation} for {resource_name}\n"
        start_time = time.time()
        
        if not self.client and self.operation in ["create_cluster", "create_nodepool", "delete_cluster"]:
            self.logs += "Error: ClusterManagerClient not initialized.\n"
            return ProberResult(success=False, logs=self.logs, latency=time.time() - start_time)

        try:
            if self.operation == "create_cluster":
                success = self._create_cluster(resource_name)
            elif self.operation == "create_nodepool":
                success = self._create_nodepool(resource_name)
            elif self.operation == "delete_cluster":
                success = self._delete_cluster(resource_name)
            elif self.operation == "deploy_app":
                success = self._deploy_app(resource_name)
            elif self.operation == "verify_app":
                success = self._verify_app(resource_name)
            else:
                self.logs += f"Unknown operation: {self.operation}\n"
                success = False
        except Exception as e:
            self.logs += f"Exception during operation: {e}\n"
            success = False

        latency = time.time() - start_time
        return ProberResult(success=success, logs=self.logs, latency=latency)

    def get_logs(self) -> str:
        return self.logs

    def _create_cluster(self, cluster_name: str) -> bool:
        self.logs += f"Creating cluster {cluster_name} in {self.location}\n"
        parent = f"projects/{self.project_id}/locations/{self.location}"
        
        cluster = container_v1.Cluster(
            name=cluster_name,
            initial_node_count=1,
            resource_labels={"label": "Daystar"}
        )
        
        request_data = {"parent": parent, "cluster": MessageToDict(cluster._pb) if MessageToDict and hasattr(cluster, '_pb') else str(cluster)}
        
        try:
            operation = self.client.create_cluster(parent=parent, cluster=cluster)
            self.logs += f"Cluster creation operation started: {operation.name}\n"
            
            response_data = MessageToDict(operation._pb) if MessageToDict and hasattr(operation, '_pb') else str(operation)
            log_api_call(cluster_name, "create_cluster", request_data, response_data)
            
            return self._wait_for_operation(cluster_name, operation.name)
        except Exception as e:
            self.logs += f"Failed to create cluster: {e}\n"
            log_api_call(cluster_name, "create_cluster", request_data, {"error": str(e)})
            return False

    def _create_nodepool(self, cluster_name: str) -> bool:
        self.logs += f"Creating nodepool for cluster {cluster_name}\n"
        parent = f"projects/{self.project_id}/locations/{self.location}/clusters/{cluster_name}"
        
        nodepool = container_v1.NodePool(
            name="default-pool",
            initial_node_count=1,
            config=container_v1.NodeConfig(
                machine_type="e2-medium",
            )
        )
        
        request_data = {"parent": parent, "node_pool": MessageToDict(nodepool._pb) if MessageToDict and hasattr(nodepool, '_pb') else str(nodepool)}
        
        try:
            operation = self.client.create_node_pool(parent=parent, node_pool=nodepool)
            self.logs += f"Nodepool creation operation started: {operation.name}\n"
            
            response_data = MessageToDict(operation._pb) if MessageToDict and hasattr(operation, '_pb') else str(operation)
            log_api_call(cluster_name, "create_node_pool", request_data, response_data)
            
            return self._wait_for_operation(cluster_name, operation.name)
        except Exception as e:
            self.logs += f"Failed to create nodepool: {e}\n"
            log_api_call(cluster_name, "create_node_pool", request_data, {"error": str(e)})
            return False

    def _delete_cluster(self, cluster_name: str) -> bool:
        self.logs += f"Deleting cluster {cluster_name}\n"
        name = f"projects/{self.project_id}/locations/{self.location}/clusters/{cluster_name}"
        
        request_data = {"name": name}
        
        try:
            operation = self.client.delete_cluster(name=name)
            self.logs += f"Cluster deletion operation started: {operation.name}\n"
            
            response_data = MessageToDict(operation._pb) if MessageToDict and hasattr(operation, '_pb') else str(operation)
            log_api_call(cluster_name, "delete_cluster", request_data, response_data)
            
            return self._wait_for_operation(cluster_name, operation.name)
        except Exception as e:
            self.logs += f"Failed to delete cluster: {e}\n"
            log_api_call(cluster_name, "delete_cluster", request_data, {"error": str(e)})
            return False

    def _wait_for_operation(self, cluster_name: str, operation_name: str) -> bool:
        self.logs += f"Waiting for operation {operation_name}...\n"
        name = f"projects/{self.project_id}/locations/{self.location}/operations/{operation_name}"
        
        while True:
            try:
                operation = self.client.get_operation(name=name)
                request_data = {"name": name}
                response_data = MessageToDict(operation._pb) if MessageToDict and hasattr(operation, '_pb') else str(operation)
                log_api_call(cluster_name, "get_operation", request_data, response_data)
                
                if operation.status == container_v1.Operation.Status.DONE:
                    if operation.error.code != 0:
                         self.logs += f"Operation failed: {operation.error.message}\n"
                         return False
                    self.logs += "Operation completed successfully.\n"
                    return True
                
                self.logs += f"Operation status: {operation.status}. Sleeping for 10s...\n"
                time.sleep(10)
            except Exception as e:
                self.logs += f"Error polling operation: {e}\n"
                return False
            
    def _deploy_app(self, cluster_name: str) -> bool:
        self.logs += f"Deploying app to cluster {cluster_name}\n"
        manifest_path = os.path.join(self.data_dir, "test-app.yaml")
        if not os.path.exists(manifest_path):
             self._create_manifest(manifest_path)
             
        cmd_cred = ["gcloud", "container", "clusters", "get-credentials", cluster_name, "--zone", self.location, "--project", self.project_id]
        self.logs += f"Running: {' '.join(cmd_cred)}\n"
        res_cred = subprocess.run(cmd_cred, capture_output=True, text=True)
        self.logs += res_cred.stdout + res_cred.stderr
        if res_cred.returncode != 0:
             self.logs += "Failed to get cluster credentials.\n"
             return False
             
        cmd_apply = ["kubectl", "apply", "-f", manifest_path]
        self.logs += f"Running: {' '.join(cmd_apply)}\n"
        res_apply = subprocess.run(cmd_apply, capture_output=True, text=True)
        self.logs += res_apply.stdout + res_apply.stderr
        if res_apply.returncode != 0:
             self.logs += "Failed to apply manifest.\n"
             return False
             
        return True
        
    def _create_manifest(self, path: str):
        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: daystar-test-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: daystar-test-app
  template:
    metadata:
      labels:
        app: daystar-test-app
    spec:
      containers:
      - name: test-app
        image: daystar-test-app:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: daystar-test-app-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: daystar-test-app
"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(manifest)
            
    def _verify_app(self, cluster_name: str) -> bool:
        self.logs += f"Verifying app in cluster {cluster_name}\n"
        cmd = ["kubectl", "get", "svc", "daystar-test-app-service", "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}"]
        self.logs += f"Running: {' '.join(cmd)}\n"
        
        for i in range(10):
            res = subprocess.run(cmd, capture_output=True, text=True)
            ip = res.stdout.strip()
            if ip:
                self.logs += f"Found LoadBalancer IP: {ip}\n"
                break
            self.logs += "Waiting for LoadBalancer IP...\n"
            time.sleep(10)
        else:
            self.logs += "Failed to get LoadBalancer IP.\n"
            return False
            
        url = f"http://{ip}/health"
        self.logs += f"Calling health endpoint: {url}\n"
        try:
            response = requests.get(url, timeout=5)
            self.logs += f"Response status: {response.status_code}\n"
            self.logs += f"Response body: {response.text}\n"
            if response.status_code == 200 and response.json().get("status") == "ok":
                return True
        except Exception as e:
            self.logs += f"Failed to call health endpoint: {e}\n"
            
        return False

    def cleanup_old_resources(self) -> bool:
        self.logs += "Scanning for old Daystar resources to clean up...\n"
        if not self.client:
            self.logs += "Error: ClusterManagerClient not initialized.\n"
            return False
            
        parent = f"projects/{self.project_id}/locations/{self.location}"
        try:
            response = self.client.list_clusters(parent=parent)
            for cluster in response.clusters:
                if cluster.resource_labels.get("label") == "Daystar":
                    self.logs += f"Found old Daystar cluster: {cluster.name}. Deleting...\n"
                    self._delete_cluster(cluster.name)
            return True
        except Exception as e:
            self.logs += f"Failed to list or delete clusters: {e}\n"
            return False
