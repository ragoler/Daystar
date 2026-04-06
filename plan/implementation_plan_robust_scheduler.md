# Implementation Plan - Robust Scheduler and Missed Step Recovery

This plan outlines changes to prevent clusters from missing steps (especially `delete_cluster`) if they are busy when the step is due, and to prevent database bloating.

## Goal
Ensure that clusters eventually execute all steps in the schedule, even if they are delayed, and prevent resource leaks.

## Research Findings
- The current scheduler looks for an exact match on `elapsed_minutes` in the schedule.
- If a cluster is processing a long step (e.g., waiting for GKE) and `is_running` is True when the next step is due, it skips it.
- If it skips the `delete_cluster` step (at Minute 25), it will never be deleted, leading to resource leakage in GKE and database bloating, which makes the UI laggy.

## Proposed Changes

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- Change the step selection logic. Instead of looking for an exact minute match, find the *latest* step in the schedule that:
    1.  Has a scheduled minute <= `elapsed_minutes`.
    2.  Has NOT been executed successfully yet for this cluster.
- We need to check the cluster's `step_logs` to see what has been executed.

```python
def get_next_step(cluster: ClusterState, schedule: Schedule, elapsed_minutes: int) -> Optional[str]:
    # iterate through schedule items in reverse (latest first)
    for item in sorted(schedule.schedule, key=lambda x: x.minute, reverse=True):
        if elapsed_minutes >= item.minute:
            # Check if this step has already succeeded
            already_done = any(log.step_name == item.step and log.status == "success" for log in cluster.step_logs)
            if not already_done:
                return item.step
    return None
```

## Verification Plan

### Automated Tests
- Create a test where a cluster is artificialy delayed and verify it eventually catches up on steps.

### Manual Verification
- Verify that old clusters (minute > 25) eventually get picked up for deletion if they missed it.
