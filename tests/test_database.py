import os
import sys
import pytest
from tinydb import TinyDB

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.database
from backend.database import init_cluster, update_cluster_step, log_api_call, get_active_clusters

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_db_path = tmp_path / "test_db.json"
    monkeypatch.setenv("DATABASE_PATH", str(test_db_path))
    
    # Re-initialize TinyDB in the module
    backend.database.DB_PATH = str(test_db_path)
    backend.database.db = TinyDB(str(test_db_path))
    backend.database.clusters_table = backend.database.db.table('clusters')
    
    yield
    
    backend.database.db.close()

def test_init_cluster():
    cluster_name = "test-cluster"
    cluster = init_cluster(cluster_name)
    
    assert cluster.name == cluster_name
    assert cluster.current_step == "initialized"
    assert cluster.status == "pending"
    assert len(cluster.step_logs) == 0
    assert len(cluster.api_logs) == 0
    
    active_clusters = get_active_clusters()
    assert len(active_clusters) == 1
    assert active_clusters[0].name == cluster_name

def test_update_cluster_step():
    cluster_name = "test-cluster"
    init_cluster(cluster_name)
    
    update_cluster_step(cluster_name, "step1", "success", "Step 1 completed")
    
    active_clusters = get_active_clusters()
    assert len(active_clusters) == 1
    cluster = active_clusters[0]
    assert cluster.current_step == "step1"
    assert cluster.status == "success"
    assert len(cluster.step_logs) == 1
    assert cluster.step_logs[0].step_name == "step1"
    assert cluster.step_logs[0].status == "success"
    assert cluster.step_logs[0].message == "Step 1 completed"

def test_log_api_call():
    cluster_name = "test-cluster"
    init_cluster(cluster_name)
    
    log_api_call(cluster_name, "/create", {"param": "value"}, {"result": "ok"})
    
    active_clusters = get_active_clusters()
    assert len(active_clusters) == 1
    cluster = active_clusters[0]
    assert len(cluster.api_logs) == 1
    assert cluster.api_logs[0].endpoint == "/create"
    assert cluster.api_logs[0].request_data == {"param": "value"}
    assert cluster.api_logs[0].response_data == {"result": "ok"}

def test_update_cluster_not_found():
    with pytest.raises(ValueError):
        update_cluster_step("non-existent", "step1", "success", "msg")

def test_log_api_call_not_found():
    with pytest.raises(ValueError):
        log_api_call("non-existent", "/create", {}, {})
