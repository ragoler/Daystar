import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We need to mock database operations because we don't have a DB initialized in tests usually,
# or we can let it use the default test DB if it creates one.
# Let's mock log_api_call to avoid DB dependency in these tests.

@pytest.fixture(autouse=True)
def mock_log_api_call():
    with patch('backend.gke_prober.log_api_call') as mock:
        yield mock

from backend.gke_prober import GkeProber
from google.cloud import container_v1

def test_gke_prober_create_cluster():
    mock_client = MagicMock()
    
    # Mock create_cluster response
    mock_op = MagicMock()
    mock_op.name = "mock-op-name"
    mock_client.create_cluster.return_value = mock_op
    
    # Mock get_operation response to end the wait loop
    mock_get_op = MagicMock()
    mock_get_op.status = container_v1.Operation.Status.DONE
    mock_get_op.error.code = 0
    mock_client.get_operation.return_value = mock_get_op
    
    with patch('google.cloud.container_v1.ClusterManagerClient', return_value=mock_client):
        prober = GkeProber(operation="create_cluster", project_id="test-project", location="us-central1")
        result = prober.execute("test-cluster")
        
        assert result.success is True
        mock_client.create_cluster.assert_called_once()
        # Verify arguments if needed, but at least assert it was called

def test_gke_prober_create_nodepool():
    mock_client = MagicMock()
    
    mock_op = MagicMock()
    mock_op.name = "mock-op-name"
    mock_client.create_node_pool.return_value = mock_op
    
    mock_get_op = MagicMock()
    mock_get_op.status = container_v1.Operation.Status.DONE
    mock_get_op.error.code = 0
    mock_client.get_operation.return_value = mock_get_op
    
    with patch('google.cloud.container_v1.ClusterManagerClient', return_value=mock_client):
        prober = GkeProber(operation="create_nodepool", project_id="test-project", location="us-central1")
        result = prober.execute("test-cluster")
        
        assert result.success is True
        mock_client.create_node_pool.assert_called_once()

def test_gke_prober_delete_cluster():
    mock_client = MagicMock()
    
    mock_op = MagicMock()
    mock_op.name = "mock-op-name"
    mock_client.delete_cluster.return_value = mock_op
    
    mock_get_op = MagicMock()
    mock_get_op.status = container_v1.Operation.Status.DONE
    mock_get_op.error.code = 0
    mock_client.get_operation.return_value = mock_get_op
    
    with patch('google.cloud.container_v1.ClusterManagerClient', return_value=mock_client):
        prober = GkeProber(operation="delete_cluster", project_id="test-project", location="us-central1")
        result = prober.execute("test-cluster")
        
        assert result.success is True
        mock_client.delete_cluster.assert_called_once()

def test_cleanup_old_resources():
    mock_client = MagicMock()
    
    # Mock list_clusters response
    mock_response = MagicMock()
    mock_cluster1 = MagicMock()
    mock_cluster1.name = "old-cluster-1"
    mock_cluster1.resource_labels = {"label": "daystar"}
    
    mock_cluster2 = MagicMock()
    mock_cluster2.name = "other-cluster"
    mock_cluster2.resource_labels = {"label": "other"}
    
    mock_response.clusters = [mock_cluster1, mock_cluster2]
    mock_client.list_clusters.return_value = mock_response
    
    # Mock delete_cluster response
    mock_op = MagicMock()
    mock_op.name = "delete-op"
    mock_client.delete_cluster.return_value = mock_op
    
    mock_get_op = MagicMock()
    mock_get_op.status = container_v1.Operation.Status.DONE
    mock_get_op.error.code = 0
    mock_client.get_operation.return_value = mock_get_op
    
    with patch('google.cloud.container_v1.ClusterManagerClient', return_value=mock_client):
        prober = GkeProber(operation="cleanup", project_id="test-project", location="us-central1")
        success = prober.cleanup_old_resources()
        
        assert success is True
        mock_client.list_clusters.assert_called_once()
        # Should delete old-cluster-1 but not other-cluster
        mock_client.delete_cluster.assert_called_once_with(name="projects/test-project/locations/us-central1/clusters/old-cluster-1")
