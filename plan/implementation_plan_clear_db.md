# Implementation Plan - Clear Database on Startup

This plan outlines changes to clear the database state on application startup to ensure a clean UI and state, as requested by the user.

## Proposed Changes

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- In `main_loop` function, after performing resource cleanup (mock or real), truncate the `clusters_table` in TinyDB.
- This will remove old rows from the UI on restart.

```python
    # Startup Cleanup
    use_mock = os.environ.get("USE_MOCK", "true").lower() == "true"
    logger.info(f"Starting startup cleanup. USE_MOCK={use_mock}")
    if use_mock:
        cleanup_resources()
    else:
        from backend.gke_prober import GkeProber
        project_id = os.environ.get("PROJECT_ID")
        location = os.environ.get("GCP_REGION", "us-central1")
        prober = GkeProber(operation="cleanup", project_id=project_id, location=location)
        prober.cleanup_old_resources()
        
    # Clear database state
    from backend.database import clusters_table
    clusters_table.truncate()
    logger.info("Purged clusters table on startup to ensure clean state.")
```

## Verification Plan

### Manual Verification
- Start the application.
- Verify that previous clusters are gone from the UI.
- Verify in logs that "Purged clusters table on startup" appears.
