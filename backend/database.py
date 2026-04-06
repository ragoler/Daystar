import datetime
import os
from typing import List
from pydantic import BaseModel
from tinydb import TinyDB, Query
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DATABASE_PATH", "data/db.json")

# Ensure directory exists
dirname = os.path.dirname(DB_PATH)
if dirname:
    os.makedirs(dirname, exist_ok=True)

try:
    db = TinyDB(DB_PATH)
    clusters_table = db.table('clusters')
except Exception as e:
    print(f"Failed to initialize database: {e}")
    raise e

class StepLog(BaseModel):
    timestamp: str
    step_name: str
    status: str
    message: str

class ApiLog(BaseModel):
    timestamp: str
    endpoint: str
    request_data: dict
    response_data: dict

class ClusterState(BaseModel):
    name: str
    created_at: str
    current_step: str
    status: str
    is_running: bool = False
    step_logs: List[StepLog] = []
    api_logs: List[ApiLog] = []

def init_cluster(name: str) -> ClusterState:
    """Initialize a new cluster record."""
    cluster = ClusterState(
        name=name,
        created_at=datetime.datetime.now().isoformat(),
        current_step="initialized",
        status="pending",
        is_running=False
    )
    clusters_table.insert(cluster.model_dump())
    return cluster

def set_cluster_running(name: str, running: bool):
    """Set cluster running state to prevent parallel execution."""
    Cluster = Query()
    result = clusters_table.search(Cluster.name == name)
    if not result:
        raise ValueError(f"Cluster {name} not found")
    
    cluster_data = result[0]
    cluster = ClusterState(**cluster_data)
    cluster.is_running = running
    
    clusters_table.update(cluster.model_dump(), Cluster.name == name)

def update_cluster_step(name: str, step: str, status: str, log_message: str):
    """Update cluster step status and append logs."""
    Cluster = Query()
    result = clusters_table.search(Cluster.name == name)
    if not result:
        raise ValueError(f"Cluster {name} not found")
    
    cluster_data = result[0]
    cluster = ClusterState(**cluster_data)
    
    step_log = StepLog(
        timestamp=datetime.datetime.now().isoformat(),
        step_name=step,
        status=status,
        message=log_message
    )
    
    cluster.current_step = step
    cluster.status = status
    cluster.step_logs.append(step_log)
    cluster.is_running = False
    
    clusters_table.update(cluster.model_dump(), Cluster.name == name)

def log_api_call(name: str, endpoint: str, request_data: dict, response_data: dict):
    """Append API Request/Response logging."""
    Cluster = Query()
    result = clusters_table.search(Cluster.name == name)
    if not result:
        raise ValueError(f"Cluster {name} not found")
    
    cluster_data = result[0]
    cluster = ClusterState(**cluster_data)
    
    api_log = ApiLog(
        timestamp=datetime.datetime.now().isoformat(),
        endpoint=endpoint,
        request_data=request_data,
        response_data=response_data
    )
    
    cluster.api_logs.append(api_log)
    
    clusters_table.update(cluster.model_dump(), Cluster.name == name)

def get_active_clusters() -> List[ClusterState]:
    """Retrieve all clusters."""
    results = clusters_table.all()
    return [ClusterState(**data) for data in results]
