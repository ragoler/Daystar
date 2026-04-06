# Implementation Plan - Resource Saving for GKE Clusters

This plan outlines changes to reduce resource usage when creating real GKE clusters, as requested by the user.

## Goal
Reduce costs and quota usage by using smaller machine types and minimizing initial node counts.

## Research Findings
- It is **not possible** to create a GKE cluster with zero node pools from the start via the API. Every cluster requires at least one node pool with at least 1 node to function.
- We can make the default node pool as small as possible by using the `e2-micro` machine type (the smallest available in the E2 family).

## Proposed Changes

### Backend

#### [Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)
- In `_create_cluster`:
    - Add `node_config` to the `Cluster` object to specify `machine_type="e2-micro"`. This ensures the default pool created with the cluster is tiny.
- In `_create_nodepool`:
    - Change `machine_type` from `e2-medium` to `e2-micro`.
    - Change the node pool name from `"default-pool"` to `"custom-pool"` to avoid collision with the default pool created by cluster creation.

```python
# In _create_cluster
cluster = container_v1.Cluster(
    name=cluster_name,
    initial_node_count=1,
    resource_labels={"label": "daystar"},
    node_config=container_v1.NodeConfig(
        machine_type="e2-micro"
    )
)

# In _create_nodepool
nodepool = container_v1.NodePool(
    name="custom-pool", # Changed from default-pool
    initial_node_count=1,
    config=container_v1.NodeConfig(
        machine_type="e2-micro",
    )
)
```

## Verification Plan

### Automated Tests
- Run tests to ensure no regression.
- We should mock these specific values in `tests/test_gke_prober.py` or just ensure they pass.

### Manual Verification
- Run a tick to create a cluster.
- Verify in GCP Console or via `gcloud container clusters describe` that the cluster uses `e2-micro` and has a `custom-pool` also using `e2-micro`.
