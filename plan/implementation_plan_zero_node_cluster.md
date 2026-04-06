# Implementation Plan - Create Cluster with 0 Nodes

This plan outlines changes to create a GKE cluster with no initial node pools (0 nodes) to save resources, based on the user's suggestion.

## Proposed Changes

### Backend

#### [Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)
- In `_create_cluster`, modify the `Cluster` object:
    - Remove `initial_node_count=1`.
    - Set `node_pools=[]` to explicitly create the cluster with no node pools.
    - Set `node_locations=[f"{self.location}-a"]` to restrict nodes to a single zone (e.g., `us-central1-a`) when a pool is added later.

```python
        cluster = container_v1.Cluster(
            name=cluster_name,
            resource_labels={"label": "daystar"},
            node_pools=[], # No initial node pools
            node_locations=[f"{self.location}-a"] # Restrict to one zone
        )
```

## Verification Plan

### Automated Tests
- Run tests to ensure no regression.
- Update tests in `test_gke_prober.py` to account for these new parameters if they assert them.

### Manual Verification
- Run a tick to create a cluster.
- Verify via `gcloud container clusters list` that the new cluster has `NUM_NODES` as `0` initially.
