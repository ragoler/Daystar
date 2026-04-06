# Walkthrough - Robust Scheduler with Missed Step Recovery

I have completed the changes to make the scheduler more robust, ensuring that clusters do not miss steps even if they are delayed or busy when the step is due.

## Changes Made

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- Replaced the exact-match `get_step_for_minute` function with **`get_next_step`**.
- The new function sorts the schedule by minute in **ascending order** (earliest first).
- It iterates through the schedule and returns the **earliest step** that should have run based on `elapsed_minutes` but has **not yet succeeded** for that cluster.
- This ensures that if a cluster is busy at minute 25 (e.g., when it should delete), it will not miss the deletion step and will pick it up on the next tick when it becomes available!

## Verification Results

### Automated Tests
Ran the full test suite to ensure no regressions and that the new logic works with the existing success path tests:
```bash
pytest
```
Output: `20 passed in 0.65s`

### Manual Verification
This should resolve the issue where clusters were living past minute 25 and bloating the database, as they will now be picked up for deletion on the first tick after they finish any previous long-running operations.
