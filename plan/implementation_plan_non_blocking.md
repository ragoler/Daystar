# Implementation Plan - Non-Blocking Manager and Cluster Locking

This plan outlines changes to prevent the manager loop from blocking when GKE operations take a long time, and to prevent race conditions by locking clusters that are currently executing a step.

## Goal
Make the manager loop non-blocking so the API and UI remain responsive during long GKE operations, and ensure a cluster doesn't try to run multiple steps at once.

## Proposed Changes

### Database

#### [Modify] [database.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/database.py)
- Add `is_running: bool = False` to `ClusterState` model.
- Add a function `set_cluster_running(name: str, running: bool)` to update this state.

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- In `process_tick`:
    - Skip clusters where `is_running` is True.
    - Set `is_running=True` before executing a step.
    - Ensure `is_running=False` is set in `update_cluster_step` or in a finally block.
- In `main_loop`:
    - Run `process_tick` as a background task using `asyncio.create_task()` instead of awaiting it. This prevents the 1-minute sleep from being delayed by long operations.

## Verification Plan

### Automated Tests
- Run tests. We might need to update tests to handle the async tasks if they assume sequential execution.

### Manual Verification
- Run in Real Mode.
- Verify that UI continues to refresh and endpoints respond while a cluster is being created (PROVISIONING).
