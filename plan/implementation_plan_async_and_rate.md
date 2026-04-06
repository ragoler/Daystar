# Implementation Plan - Async Ops and 3-Minute Cluster Creation

This plan outlines changes to make GKE operations asynchronous and to limit automatic cluster creation to once every 3 minutes, while maintaining 1-minute resolution for the scheduler.

## Proposed Changes

### Backend

#### [Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)
- In `_create_cluster`, remove `_wait_for_operation` and return `True` immediately.
- In `_create_nodepool`, remove `_wait_for_operation` and return `True` immediately.

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- Add a global counter or use a timestamp to track ticks.
- In `process_tick`, modify the auto-creation logic to trigger only every 3 ticks (minutes), starting at tick 1.
- Example logic:
  ```python
  # Global or passed counter
  if (tick_count - 1) % 3 == 0:
      init_cluster(...)
  ```

### Configuration

#### [Modify] [schedule.yaml](file:///Users/ragoler/Documents/JetSki/Daystar/data/schedule.yaml)
- Adjust intervals to account for async operations:
    - Minute 1: `create_cluster`
    - Minute 12: `verify_cluster` (Allow ~10 mins for creation)
    - Minute 13: `create_nodepool`
    - Minute 18: `deploy_app` (Allow ~5 mins for nodepool)
    - Minute 20: `ping_app`
    - Minute 25: `delete_cluster`

## Verification Plan

### Manual Verification
- Run the system.
- Verify that a new cluster is created only on ticks 1, 4, 7...
- Verify that `create_cluster` step shows success immediately in UI.
