# Implementation Plan - Startup Cleanup

This plan outlines changes to implement resource cleanup on application startup, to ensure no leftover clusters from previous runs remain.

## Proposed Changes

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- In `main_loop` function, before entering the infinite loop, call the appropriate cleanup function based on `USE_MOCK`.
- This ensures that every time the manager starts, it cleans up old resources.

```python
async def main_loop():
    """Main scheduling loop."""
    schedule = load_schedule()
    logger.info(f"Loaded schedule: {schedule}")
    
    # Startup Cleanup
    use_mock = os.environ.get("USE_MOCK", "true").lower() == "true"
    logger.info(f"Starting startup cleanup. USE_MOCK={use_mock}")
    if use_mock:
        cleanup_resources()
    else:
        from backend.gke_prober import GkeProber
        project_id = os.environ.get("PROJECT_ID")
        location = os.environ.get("GCP_REGION", "us-central1")
        # GkeProber needs operation, project_id, location
        prober = GkeProber(operation="cleanup", project_id=project_id, location=location)
        prober.cleanup_old_resources()
        
    while True:
        await process_tick(schedule, datetime.datetime.now())
        await asyncio.sleep(60)
```

## Verification Plan

### Manual Verification
- Set `USE_MOCK=true`.
- Create a dummy file in `data/mock_resources/`.
- Start the application.
- Verify in logs that cleanup is triggered and the file is deleted.
