# Implementation Plan - Load .env file (using python-dotenv)

This plan outlines changes to load environment variables from the `.env` file using the `python-dotenv` package, as requested by the user.

## Proposed Changes

### Dependencies

#### [Modify] [requirements.txt](file:///Users/ragoler/Documents/JetSki/Daystar/requirements.txt)
- Add `python-dotenv`.

### Backend

#### [Modify] [database.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/database.py)
- Import `load_dotenv` from `dotenv`.
- Call `load_dotenv()` at the top of the file to load environment variables from `.env`.

```python
from dotenv import load_dotenv
load_dotenv()
```

## Verification Plan

### Automated Tests
- Run tests to ensure no regression.

### Manual Verification
- Install new dependency: `./venv/bin/pip install -r requirements.txt`.
- Set `USE_MOCK=false` in `.env`.
- Restart the server.
- Verify in logs that it attempts to use `GkeProber` (it will log "Starting GKE operation" instead of "Starting mock execution").
