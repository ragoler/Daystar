import asyncio
import datetime
import os
import pytest
from tinydb import TinyDB
import backend.database
import backend.manager
from backend.database import init_cluster, get_active_clusters, clusters_table
from backend.manager import process_tick, Schedule, ScheduleItem

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

@pytest.fixture
def test_schedule():
    return Schedule(schedule=[
        ScheduleItem(minute=1, step="create_cluster"),
        ScheduleItem(minute=5, step="verify_cluster"),
        ScheduleItem(minute=10, step="deploy_app"),
        ScheduleItem(minute=15, step="delete_cluster")
    ])

def test_full_lifecycle_success(test_schedule, tmp_path, monkeypatch):
    # Mock MockProber to be fast and deterministic
    mock_dir = tmp_path / "mock_resources"
    os.makedirs(mock_dir, exist_ok=True)
    
    class PatchedMockProber(backend.manager.MockProber):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, data_dir=str(mock_dir), failure_rate=0.0, sleep_delay=0.0)
            
    monkeypatch.setattr(backend.manager, "MockProber", PatchedMockProber)
    
    # Also patch cleanup_resources to use mock_dir
    def patched_cleanup():
        if os.path.exists(mock_dir):
            for f in os.listdir(mock_dir):
                os.remove(os.path.join(mock_dir, f))
    monkeypatch.setattr(backend.manager, "cleanup_resources", patched_cleanup)
    monkeypatch.setattr(backend.manager, "SAFETY_LIMIT", 20)
    monkeypatch.setenv("USE_MOCK", "true")

    # Initialize a cluster
    cluster_name = "e2e-test-cluster"
    cluster = init_cluster(cluster_name)
    created_at = datetime.datetime.fromisoformat(cluster.created_at)
    
    # Simulate 15 minutes of ticks
    for minute in range(1, 17): # Run up to minute 16 to ensure delete happens and we can check state after
        tick_time = created_at + datetime.timedelta(minutes=minute)
        asyncio.run(process_tick(test_schedule, tick_time))
        
        # Verify state at specific minutes
        clusters = get_active_clusters()
        test_cluster = next((c for c in clusters if c.name == cluster_name), None)
        assert test_cluster is not None
        
        assert len(clusters) == 1 + ((minute - 1) // 3 + 1)
        
        if minute < 1:
            assert test_cluster.current_step == "initialized"
        elif minute in range(1, 5):
            assert test_cluster.current_step == "create_cluster"
        elif minute in range(5, 10):
            assert test_cluster.current_step == "verify_cluster"
        elif minute in range(10, 15):
            assert test_cluster.current_step == "deploy_app"
            
    # Let's check the final state in DB
    clusters = get_active_clusters()
    test_cluster = next((c for c in clusters if c.name == cluster_name), None)
    assert test_cluster is not None
    assert test_cluster.current_step == "delete_cluster"
    assert test_cluster.status == "success"
    
    # Verify that mock file was created
    assert os.path.exists(mock_dir / f"{cluster_name}.mock")

def test_safety_limit_triggered_e2e(test_schedule, tmp_path, monkeypatch):
    # Mock SAFETY_LIMIT to a small number
    monkeypatch.setattr(backend.manager, "SAFETY_LIMIT", 2)
    
    mock_dir = tmp_path / "mock_resources"
    os.makedirs(mock_dir, exist_ok=True)
    
    class PatchedMockProber(backend.manager.MockProber):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, data_dir=str(mock_dir), failure_rate=0.0, sleep_delay=0.0)
            
    monkeypatch.setattr(backend.manager, "MockProber", PatchedMockProber)
    
    def patched_cleanup():
        if os.path.exists(mock_dir):
            for f in os.listdir(mock_dir):
                os.remove(os.path.join(mock_dir, f))
    monkeypatch.setattr(backend.manager, "cleanup_resources", patched_cleanup)

    # Initialize 3 clusters (exceeding limit of 2)
    init_cluster("c1")
    init_cluster("c2")
    init_cluster("c3")
    
    # Create a mock file to verify deletion
    with open(mock_dir / "c1.mock", "w") as f:
        f.write("test")
        
    # Run a tick
    asyncio.run(process_tick(test_schedule))
    
    # Verify DB purged
    clusters = get_active_clusters()
    assert len(clusters) == 0
    
    # Verify file deleted
    assert not os.path.exists(mock_dir / "c1.mock")
