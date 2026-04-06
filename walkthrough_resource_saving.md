# Walkthrough - Resource Saving for GKE Clusters

I have completed the changes to reduce resource usage when creating real GKE clusters.

## Changes Made

### GKE Prober
- **[Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)**:
    - Updated `_create_cluster` to explicitly configure the default node pool to use the **`e2-micro`** machine type (the smallest available).
    - Updated `_create_nodepool` to also use **`e2-micro`** and renamed the new pool to **`custom-pool`** to avoid colliding with the default pool.

## Verification Results

### Automated Tests
Ran the unit tests for the prober to ensure the changes didn't break anything:
```bash
./venv/bin/pytest tests/test_gke_prober.py
```
Output: `4 passed in 0.33s`

The full test suite also passes.

### Manual Verification
On the next tick that triggers cluster creation, the system will now request `e2-micro` instances, which should significantly reduce cost and quota usage.
