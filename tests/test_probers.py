import sys
import os
import pytest
import time

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.probers import MockProber, ProberResult

def test_mock_prober_success(tmp_path):
    data_dir = tmp_path / "data"
    prober = MockProber(failure_rate=0.0, sleep_delay=0.1, data_dir=str(data_dir))
    
    result = prober.execute("test-cluster")
    
    assert result.success is True
    assert "succeeded" in result.logs
    assert result.latency >= 0.1
    
    # Check if file was created
    file_path = data_dir / "test-cluster.mock"
    assert file_path.exists()

def test_mock_prober_failure(tmp_path):
    data_dir = tmp_path / "data"
    prober = MockProber(failure_rate=1.0, sleep_delay=0.1, data_dir=str(data_dir))
    
    result = prober.execute("test-cluster")
    
    assert result.success is False
    assert "failure" in result.logs or "Failed" in result.logs
    
    # Check if file was cleaned up on failure (based on my implementation)
    file_path = data_dir / "test-cluster.mock"
    assert not file_path.exists()

def test_mock_prober_logs(tmp_path):
    data_dir = tmp_path / "data"
    prober = MockProber(failure_rate=0.0, sleep_delay=0.0, data_dir=str(data_dir))
    
    prober.execute("test-cluster")
    logs = prober.get_logs()
    
    assert "Starting mock execution" in logs
    assert "succeeded" in logs
