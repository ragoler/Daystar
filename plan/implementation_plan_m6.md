# Implementation Plan - Milestone 6: UI Development

This plan outlines the steps to build the premium status grid UI for the Daystat project.

## User Environment
OS: mac
Workspace: `/Users/ragoler/Documents/JetSki/Daystar`

## Proposed Changes

### 1. Static Files Structure
Create the following files in `frontend/`:
- `index.html`: Main structure of the UI.
- `style.css`: Dark theme, glassmorphism effects, and responsive grid layout.
- `app.js`: Logic for fetching data, rendering the grid, polling, and tooltips.

### 2. Backend Updates (FastAPI)
- Modify `backend/main.py` to serve static files from `frontend/`.
- Add a fallback to `index.html` for single-page app behavior if needed, or just map `/` to `frontend/index.html`.

### 3. UI Design & Layout
- **Theme**: Dark mode with glassmorphism (translucent backgrounds, blur effects).
- **Grid**:
    - **Columns**: Steps defined in `data/schedule.yaml` (`create_cluster`, `verify_cluster`, `create_nodepool`, `deploy_app`, `ping_app`, `delete_cluster`).
    - **Rows**: Time ticks. We will aggregate data by time ticks (e.g., rounded to minutes) to show what happened at each tick.
- **Interactions**:
    - Status icons (green check, red cross).
    - Hover on status cells to show a popover with detailed logs and API request/response data.

### 4. Implementation Steps

#### Step 4.1: Create Frontend Files
- Create `frontend/index.html` with basic layout and containers for the grid.
- Create `frontend/style.css` with dark theme variables and grid styles.
- Create `frontend/app.js` with placeholders for data fetching and rendering.

#### Step 4.2: Update Backend to Serve Static Files
- Use `FastAPI.mount` or `FileResponse` to serve `frontend/` directory.

#### Step 4.3: Implement Grid Logic in `app.js`
- Fetch schedule from `/status` (need to ensure schedule info is available or hardcode it based on `schedule.yaml`).
- Fetch cluster states from `/status`.
- Process data to map clusters to rows (time) and columns (steps).
- Render the grid.

#### Step 4.4: Polling & UI Enhancements
- Implement 5-second polling for live updates.
- Add hover tooltips for logs.

## Verification Plan

### Automated Tests
- Add a test in `tests/test_health.py` (or a new file) to verify static file serving returns 200 OK for `index.html`.

### Manual Verification
- Open `http://localhost:8000` in browser.
- Verify the grid renders rows and columns correctly.
- Verify dark theme and glassmorphism styling.
- Verify tooltips appear on hover.
