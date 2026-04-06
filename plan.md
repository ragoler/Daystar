# Daystat: GKE Prober Monitoring System Specification

## Overview
Daystat is an autonomous monitoring system designed to probe the reliability and performance of Google Kubernetes Engine (GKE) by continuously executing full lifecycle operations on clusters and applications. It ensures that the control plane and data plane are functioning correctly by performing real-world operations.

## Core Functionality

### The Prober & Lifecycle
The system acts as a prober that executes a linear sequence of steps on GKE resources.
- **Incremental Ticks**: The system triggers a new execution flow every 1 minute.
- **Parallelism**: Multiple clusters will be active at any given time, each at a different stage of its lifecycle.
- **Resource Labeling**: All resources created by this system will be labeled with `label: Daystar` to ensure safe management and cleanup.
- **Initialization**: On application startup, the system will identify and purge all existing resources with the `Daystar` label to ensure a clean state.
- **Safety Mechanism**: If the system detects that it needs to create more clusters than expected (exceeding the expected count based on lifecycle duration), it will delete all clusters with the "Daystar" label and restart monitoring from the beginning.

#### Example Lifecycle Timeline (Strictly Ordered)
Operations must follow a strict sequence. Verification steps are required to gate subsequent operations.
- **Minute 1**: Trigger Cluster Creation.
- **Minute 5** (Example): Verify Cluster Creation Succeeded.
- **Minute 6**: Trigger Nodepool Creation.
- **Minute 9** (Example): Verify Nodepool Creation Succeeded.
- **Minute 10**: Deploy a simple app.
- **Minute 12**: Ping the app to validate responsiveness.
- **Minute 15**: Delete the cluster (Must always be the final step).

In this example, up to 15 clusters could be running or transitioning in parallel.

### Extensibility & Step Definition
- **Flexible System**: Steps can be added or modified at designated minute intervals.
- **Step Contract**: Each step is a defined function that:
    - Executes the specific GKE operation.
    - Reports the outcome (Success/Failure).
    - Captures and logs the raw HTTP request and response to the GKE API for debugging.

## System Architecture

The following components will make up the system:
1. **Probers**: Parent prober component that calls GKE APIs, executes `kubectl` commands, and calls the simple test app.
2. **System Manager**: Runs the simulation every minute. It triggers probers with the cluster name and step, governed by a configuration file.
3. **ORM Layer**: Handles interaction with the lightweight database (e.g., TinyDB).
4. **FastAPI**: Provides APIs to serve information to the UI.
5. **UI**: The HTML, CSS, and JS interface for visualization (separated from the monitoring process).
6. **Testing System**: Unit tests and component tests for all parts of the system.
7. **Simple Test App**: A separate app for one-time image creation, deployed on the test clusters to validate functionality.

The system will support running locally on a Mac for development and testing, and later deployed to a GKE cluster in the cloud.

## UI Requirements

### The Grid View
The UI will feature a status grid to visualize the pipeline.
- **Rows**: Represent time ticks in `hh:mm` format.
- **Columns**: Represent the lifecycle steps (e.g., Create Cluster, Create Nodepool, Deploy, Validate, Delete).
- **Cells**: Display the status of a specific cluster at that time and step.
    - **Green Checkmark**: Operation succeeded.
    - **Red Checkmark/Cross**: Operation failed.
- **Hover Interactions**: Hovering over a status indicator will reveal a popover/tooltip containing:
    - Detailed logs for that step.
    - The HTTP request and response details sent to the GKE API.

### Design & Aesthetics
To provide a premium experience:
- **Theme**: Curated dark mode with glassmorphism effects.
- **Grid Layout**: Responsive CSS Grid with smooth scrolling.
- **Animations**: Subtle micro-animations for status state changes and hover effects.
- **Typography**: Modern sans-serif font (e.g., Inter or Outfit).

## Technology Stack

### Backend
- **Core**: Python with FastAPI for the API and static file serving.
- **Scheduler**: A robust background task manager (or custom cron loop) to handle the 1-minute increments.
- **Client**: Google Cloud Python SDK for GKE.
- **Database**: TinyDB (or similar lightweight JSON database) to capture state. Persistence reliability over time is not critical.
- **ORM**: A simple ORM layer to abstract database interactions.

### Frontend
- **Structure**: HTML5.
- **Styling**: Vanilla CSS (no Tailwind unless requested).
- **Logic**: Vanilla JavaScript for dynamic grid rendering and hover state management.

## Open Considerations
- **GKE Quotas**: Creating clusters every minute will quickly hit project quotas. We need to assess the limits and potentially use a small max concurrent clusters limit or clean up aggressively.
- **Cluster Creation Time**: GKE clusters typically take 5-10 minutes to become fully ready. The schedule must account for this latency.

## Milestones

Everything must be developed and tested within a Python virtual environment (`venv`).

### Milestone 1: Environment & Core Scaffolding
- **Assigned Agent**: Agent A (Core)
- **Dependencies**: None
- **Goal**: Setup the development environment and the basic FastAPI structure.
- **Technical Details**:
    - Framework: FastAPI (`fastapi.FastAPI()`)
    - Server: Uvicorn (`uvicorn.run()`)
    - Testing: `pytest`
- **Tasks**:
    - [ ] Create project root and target directory structure: `backend/`, `frontend/`, `tests/`, `data/`.
    - [ ] Initialize Python virtual environment: `python3 -m venv venv`.
    - [ ] Activate virtual environment and install dependencies.
    - [ ] Create `requirements.txt` with `fastapi`, `uvicorn`, `pytest`, `pydantic`, `tinydb`, `requests`.
    - [ ] Setup structured logging configuration in `backend/logging_config.py`.
    - [ ] Implement `backend/main.py` with a simple `/health` endpoint.
    - [ ] Configure CORS in FastAPI for local frontend development.
    - [ ] Setup testing skeleton in `tests/test_health.py`.
    - [ ] Create basic `.gitignore` for Python, venv, and data files.
    - [ ] Verify environment by running tests in the venv.
- **Exit Criteria / Testing**:
    - **Automated**: Run `pytest` to verify that the `/health` endpoint returns `{"status": "ok"}`.
    - **Manual**: Start the server and access `http://localhost:8000/health` via curl.

### Milestone 2: State Persistence (TinyDB & ORM)
- **Assigned Agent**: Agent A (Core)
- **Dependencies**: Milestone 1
- **Goal**: Implement the database and ORM layer to capture state.
- **Technical Details**:
    - Database: `tinydb.TinyDB('data/db.json')`
- **Tasks**:
    - [ ] Ensure `data/` directory exists for database file.
    - [ ] Initialize TinyDB instance in a dedicated database module.
    - [ ] Define Pydantic model for full Cluster State (Name, Current Step, Status).
    - [ ] Define Pydantic model for Step execution logs.
    - [ ] Define Pydantic model for API Request/Response logging.
    - [ ] Implement ORM method to initialize a new cluster record.
    - [ ] Implement ORM method to update cluster step status and append logs.
    - [ ] Implement ORM method to retrieve all active clusters for the grid view.
    - [ ] Add exception handling for database file access.
    - [ ] Write unit tests in `tests/test_database.py` for all ORM operations.
- **Exit Criteria / Testing**:
    - **Automated**: Test script that writes a mock cluster state and reads it back successfully.
    - **Manual**: Verify that the JSON file generated by TinyDB contains the expected data.

### Milestone 3: The Prober Interface & Mock Implementation
- **Assigned Agent**: Agent B (Prober)
- **Dependencies**: Milestone 1
- **Goal**: Build the prober framework and a test application.
- **Technical Details**:
    - Interface: Python `abc` (Abstract Base Classes).
- **Tasks**:
    - [ ] Define the base `BaseProber` class with abstract methods: `execute()`, `get_logs()`.
    - [ ] Define standard return types for prober execution (success, logs, latency).
    - [ ] Implement `MockProber` that simulates file creation and latency on GKE.
    - [ ] Add random failure injection to `MockProber` to test error paths.
    - [ ] Add configurable sleep delays to `MockProber` to simulate execution time.
    - [ ] Create a simple "Hello World" app code (e.g., in Python) to be used for validation.
    - [ ] Create a Dockerfile for the simple test app.
    - [ ] Write a script to build and push (or load) the test app image.
    - [ ] Ensure the test app can respond to a specific health endpoint or payload.
    - [ ] Write unit tests for the interface and mock prober in `tests/test_probers.py`.
- **Exit Criteria / Testing**:
    - **Automated**: Unit test asserting that the `MockProber` returns success/failure and logs as expected.
    - **Manual**: Build and run the simple test app locally.

### Milestone 4: System Manager & Scheduler
- **Assigned Agent**: Agent A (Core)
- **Dependencies**: Milestone 2, Milestone 3
- **Goal**: Implement the 1-minute tick monitoring loop and state machine.
- **Technical Details**:
    - Scheduler: `asyncio` sleep loop or `apscheduler`.
- **Tasks**:
    - [ ] Create `backend/manager.py` for central orchestration.
    - [ ] Implement logic to load schedule configuration from a YAML file.
    - [ ] Define the outer scheduling loop matching the 1-minute increments.
    - [ ] Implement the state machine that calculates what step a cluster is on.
    - [ ] Add logic to call the appropriate Prober based on the current step.
    - [ ] Implement the safety check: count active clusters in parallel.
    - [ ] Implement target cleanup logic if safety limits are exceeded.
    - [ ] Integrate DB updates (save state) into the execution loop.
    - [ ] Add detailed execution logging for manager metrics.
    - [ ] Write unit tests for manager logic using mock probers in `tests/test_manager.py`.
- **Exit Criteria / Testing**:
    - **Automated**: Test simulation that runs for mock 5 minutes (fast-forwarded) and verifies correct prober calls.
    - **Manual**: Run the manager for 3 minutes with mock probers and watch terminal output.

### Milestone 5: Real GKE Integration
- **Assigned Agent**: Agent B (Prober)
- **Dependencies**: Milestone 3
- **Goal**: Connect to GKE API and execute real operations.
- **Technical Details**:
    - SDK: `google-cloud-container` (`google.cloud.container_v1.ClusterManagerClient`).
- **Tasks**:
    - [ ] Add `google-cloud-container` to `requirements.txt`.
    - [ ] Implement GKE cluster creation logic in a dedicated prober class.
    - [ ] Implement GKE node pool creation logic.
    - [ ] Implement GKE cluster deletion logic.
    - [ ] Implement operation polling to wait for cluster/nodepool transitions.
    - [ ] Implement `kubectl` integration (via subprocess) for app deployment.
    - [ ] Create YAML manifests for the simple app deployment.
    - [ ] Implement application health validation via HTTP calls.
    - [ ] Add API request/response logging for all SDK calls to state DB.
    - [ ] Implement startup clean-up scan for "Daystar" labeled clusters.
- **Exit Criteria / Testing**:
    - **Automated**: Unit tests with SDK mocks proving API calls are constructed correctly.
    - **Manual**: Run startup cleanup and verify it deletes a test cluster labeled "Daystar".

### Milestone 6: UI Development
- **Assigned Agent**: Agent C (Frontend)
- **Dependencies**: Milestone 4
- **Goal**: Build the premium status grid interface.
- **Technical Details**:
    - Grid: CSS Grid layout.
    - Style: Glassmorphism filters, dark theme.
- **Tasks**:
    - [ ] Create static files structure under `frontend/` (HTML, CSS, JS).
    - [ ] Build the base grid layout (Rows = Time, Cols = Steps).
    - [ ] Implement CSS dark theme and glassmorphism styling effects.
    - [ ] Implement JS `fetch()` to pull data from FastAPI status endpoints.
    - [ ] Create polling mechanism in JS for auto-refresh.
    - [ ] Implement popover tooltips for displaying logs on hover.
    - [ ] Add status icons (green check, red cross) based on DB values.
    - [ ] Format dates and times to standard `hh:mm` format in UI.
    - [ ] Add loading indicators or skeleton screens.
    - [ ] Handle disconnected states gracefully with a visual indicator.
- **Exit Criteria / Testing**:
    - **Automated**: Test health check of static file serving.
    - **Manual**: Open UI in browser, verify rows are minutes and columns are steps.

### Milestone 7: E2E Testing & Hardening
- **Assigned Agent**: Agent D (QA)
- **Dependencies**: Milestone 5, Milestone 6
- **Goal**: Validate the end-to-end flow and safety mechanisms.
- **Tasks**:
    - [ ] Setup full integration test environment.
    - [ ] Write integration test for full mocked lifecycle (15 mins compressed).
    - [ ] Write test validating safety limit interventions.
    - [ ] Optimize database queries for rendering dashboard data fast.
    - [ ] Add performance telemetry to the manager loop.
    - [ ] Create Dockerfile for deploying the completed prober monitoring system.
    - [ ] Prepare K8s manifests for the prober deployment.
    - [ ] Perform security review of allowed commands running in subprocess.
    - [ ] Finalize README documentation with setup and run instructions.
- **Exit Criteria / Testing**:
    - **Automated**: Passing full suite of unit and integration tests.

