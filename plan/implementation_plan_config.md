# Implementation Plan - Configuration for Mock/Real Mode

This plan outlines changes to allow switching between Mock and Real GKE probers via environment variables, and documents the `.env` file.

## Proposed Changes

### Configuration

#### [Modify] [.env](file:///Users/ragoler/Documents/JetSki/Daystar/.env)
- Add `USE_MOCK=true` (default to true for safety).
- Add comments explaining each variable.

#### [NEW] [.env.example](file:///Users/ragoler/Documents/JetSki/Daystar/.env.example)
- Create a template file with documentation and dummy values to be committed.

### Backend

#### [Modify] [manager.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/manager.py)
- Read `USE_MOCK` environment variable.
- In `process_tick`, switch between `MockProber` and `GkeProber` based on `USE_MOCK`.
- Pass `PROJECT_ID` and `GCP_REGION` to `GkeProber` if in real mode.

```python
            use_mock = os.environ.get("USE_MOCK", "true").lower() == "true"
            if use_mock:
                prober = MockProber()
            else:
                from backend.gke_prober import GkeProber
                project_id = os.environ.get("PROJECT_ID")
                location = os.environ.get("GCP_REGION", "us-central1")
                prober = GkeProber(operation=step, project_id=project_id, location=location)
```

## Verification Plan

### Automated Tests
- Run existing E2E tests (they mock `MockProber` anyway, so they should still pass if `USE_MOCK` defaults to true or is forced to true in tests).
- We should ensure tests force `USE_MOCK=true` or mock the prober regardless of environment. The tests currently patch `backend.manager.MockProber`, so they should be safe if we maintain that structure or patch `GkeProber` too if we add it.

### Manual Verification
- Set `USE_MOCK=true` and verify mock flies are created.
- Set `USE_MOCK=false` (with real project ID) and verify it attempts to call GKE (or fails with permission if not auth, but should show different logs than mock).
