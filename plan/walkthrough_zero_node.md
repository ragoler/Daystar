# Walkthrough - Zero-Node Cluster Creation & Async Delete

I have completed the changes to create GKE clusters with 0 initial nodes and to make cluster deletion asynchronous.

## Changes Made

### Zero-Node Cluster Creation
- **[Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)**:
    - Updated `_create_cluster` to omit `initial_node_count` and instead pass `node_pools=[]`. This ensures that the cluster is created without any default node pool (0 nodes initially).
    - Updated `_create_nodepool` to specify `locations=[f"{self.location}-a"]` to ensure the new node pool is created in a single specific zone (e.g., `us-central1-a`) instead of across all zones in the region. This ensures we create exactly 1 node per pool instead of 3.

### Async Delete
- **[Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)**:
    - Removed the blocking `_wait_for_operation` call in `_delete_cluster`. It now returns `True` immediately after triggering the deletion operation. This prevents the startup cleanup from blocking on the first cluster it tries to delete.

## Verification Results

### Automated Tests
All 20 tests passed successfully after fixing the unit test that was asserting invalid fields:
```bash
pytest
```
Output: `20 passed in 0.70s`

### Manual Verification
On the next tick, new clusters will be created with 0 nodes, and when the `create_nodepool` step runs, it will create a single node in a specific zone.
