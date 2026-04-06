# Implementation Plan - Asynchronous GKE Operations

This plan outlines changes to make GKE operations return immediately (fire and forget) to show quick progress in the UI, and adjusts the schedule to account for actual creation times.

## Proposed Changes

### Backend

#### [Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)
- In `_create_cluster`, remove the call to `_wait_for_operation` and return `True` immediately after the creation operation is triggered successfully.
- In `_create_nodepool`, remove the call to `_wait_for_operation` and return `True` immediately after the nodepool creation operation is triggered.

#### [Modify] [schedule.yaml](file:///Users/ragoler/Documents/JetSki/Daystar/data/schedule.yaml)
- Adjust intervals to give GKE time to create resources between steps.
- Proposed Schedule:
    - Minute 1: `create_cluster`
    - Minute 12: `verify_cluster` (Allow ~10 mins for cluster creation)
    - Minute 13: `create_nodepool`
    - Minute 18: `deploy_app` (Allow ~5 mins for nodepool creation)
    - Minute 20: `ping_app`
    - Minute 25: `delete_cluster`

## Verification Plan

### Manual Verification
- Run the system with the new schedule.
- Verify that `create_cluster` column turns green immediately in the UI on the next tick after initialization.
- Verify that subsequent steps succeed when their scheduled time arrives.
