import asyncio
import datetime
import os
import pytest
from tinydb import TinyDB
import backend.database
import backend.manager
from backend.database import init_cluster, get_active_clusters, clusters_table
from backend.manager import process_tick, load_schedule, Schedule, ScheduleItem

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_db_path = tmp_path / "test_db.json"
    monkeypatch.setenv("DATABASE_PATH", str(test_db_path))
    monkeypatch.setenv("USE_MOCK", "true")
    
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
        ScheduleItem(minute=5, step="verify_cluster")
    ])

def test_process_tick(test_schedule, tmp_path, monkeypatch):
    # Mock MockProber data_dir
    mock_dir = tmp_path / "mock_resources"
    os.makedirs(mock_dir, exist_ok=True)
    
    class PatchedMockProber(backend.manager.MockProber):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, data_dir=str(mock_dir), failure_rate=0.0)
            self.sleep_delay = 0
            
    monkeypatch.setattr(backend.manager, "MockProber", PatchedMockProber)
    
    # Initialize a cluster
    cluster_name = "test-cluster"
    cluster = init_cluster(cluster_name)
    
    # Simulate tick at minute 1
    created_at = datetime.datetime.fromisoformat(cluster.created_at)
    tick_time = created_at + datetime.timedelta(minutes=1)
    
    # Mock init_cluster to avoid creating automatic clusters in test
    monkeypatch.setattr(backend.manager, "init_cluster", lambda name: None)
    
    asyncio.run(process_tick(test_schedule, tick_time))
    
    # Verify state
    clusters = get_active_clusters()
    assert len(clusters) == 1
    assert clusters[0].current_step == "create_cluster"
    assert clusters[0].status == "success"
    
    # Simulate tick at minute 5
    tick_time = created_at + datetime.timedelta(minutes=5)
    asyncio.run(process_tick(test_schedule, tick_time))
    
    # Verify state
    clusters = get_active_clusters()
    assert len(clusters) == 1
    assert clusters[0].current_step == "verify_cluster"

def test_safety_check(test_schedule, tmp_path, monkeypatch):
    # Mock SAFETY_LIMIT to a small number for testing
    monkeypatch.setattr(backend.manager, "SAFETY_LIMIT", 2)
    
    mock_dir = tmp_path / "mock_resources"
    os.makedirs(mock_dir, exist_ok=True)
    
    class PatchedMockProber(backend.manager.MockProber):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, data_dir=str(mock_dir), failure_rate=0.0)
            self.sleep_delay = 0
            
    monkeypatch.setattr(backend.manager, "MockProber", PatchedMockProber)
    
    # Also patch cleanup_resources to use mock_dir
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
        
    asyncio.run(process_tick(test_schedule))
    
    # Verify DB purged
    clusters = get_active_clusters()
    assert len(clusters) == 0
    
    # Verify file deleted
    assert not os.path.exists(mock_dir / "c1.mock")
