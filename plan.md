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
    - [x] Create project root and target directory structure: `backend/`, `frontend/`, `tests/`, `data/`.
    - [x] Initialize Python virtual environment: `python3 -m venv venv`.
    - [x] Activate virtual environment and install dependencies.
    - [x] Create `requirements.txt` with `fastapi`, `uvicorn`, `pytest`, `pydantic`, `tinydb`, `requests`.
    - [x] Setup structured logging configuration in `backend/logging_config.py`.
    - [x] Implement `backend/main.py` with a simple `/health` endpoint.
    - [x] Configure CORS in FastAPI for local frontend development.
    - [x] Setup testing skeleton in `tests/test_health.py`.
    - [x] Create basic `.gitignore` for Python, venv, and data files.
    - [x] Verify environment by running tests in the venv.
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
    - [x] Ensure `data/` directory exists for database file.
    - [x] Initialize TinyDB instance in a dedicated database module.
    - [x] Define Pydantic model for full Cluster State (Name, Current Step, Status).
    - [x] Define Pydantic model for Step execution logs.
    - [x] Define Pydantic model for API Request/Response logging.
    - [x] Implement ORM method to initialize a new cluster record.
    - [x] Implement ORM method to update cluster step status and append logs.
    - [x] Implement ORM method to retrieve all active clusters for the grid view.
    - [x] Add exception handling for database file access.
    - [x] Write unit tests in `tests/test_database.py` for all ORM operations.
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
    - [x] Define the base `BaseProber` class with abstract methods: `execute()`, `get_logs()`.
    - [x] Define standard return types for prober execution (success, logs, latency).
    - [x] Implement `MockProber` that simulates file creation and latency on GKE.
    - [x] Add random failure injection to `MockProber` to test error paths.
    - [x] Add configurable sleep delays to `MockProber` to simulate execution time.
    - [x] Create a simple "Hello World" app code (e.g., in Python) to be used for validation.
    - [x] Create a Dockerfile for the simple test app.
    - [x] Write a script to build and push (or load) the test app image.
    - [x] Ensure the test app can respond to a specific health endpoint or payload.
    - [x] Write unit tests for the interface and mock prober in `tests/test_probers.py`.
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
    - [x] Create `backend/manager.py` for central orchestration.
    - [x] Implement logic to load schedule configuration from a YAML file.
    - [x] Define the outer scheduling loop matching the 1-minute increments.
    - [x] Implement the state machine that calculates what step a cluster is on.
    - [x] Add logic to call the appropriate Prober based on the current step.
    - [x] Implement the safety check: count active clusters in parallel.
    - [x] Implement target cleanup logic if safety limits are exceeded.
    - [x] Integrate DB updates (save state) into the execution loop.
    - [x] Add detailed execution logging for manager metrics.
    - [x] Write unit tests for manager logic using mock probers in `tests/test_manager.py`.
- **Exit Criteria / Testing**:
    - **Automated**: Test simulation that runs for mock 5 minutes (fast-forwarded) and verifies correct prober calls.
    - **Manual**: Run the manager for 3 minutes with mock probers and watch terminal output.

#### Detailed Implementation Plan (Merged from implementation_plan_m4.md)

**User Review Required**
- Add `pyyaml` to `requirements.txt` to support schedule configuration.
- Add `created_at` field to `ClusterState` model in `database.py` to calculate elapsed time.

**Proposed Changes**
- **Dependencies**: Add `pyyaml`.
- **Database Module**: Modify `backend/database.py` (add `created_at`, update `init_cluster`).
- **Configuration**: Create `data/schedule.yaml` to define the steps and their minute offsets.
- **System Manager**: Create `backend/manager.py` (async loop, state machine, safety check).
- **Testing**: Create `tests/test_manager.py` with mock probers.

**Open Questions**
- Default safety limit set to 15 clusters based on user selection.

### Milestone 5: Real GKE Integration
- **Assigned Agent**: Agent B (Prober)
- **Dependencies**: Milestone 3
- **Goal**: Connect to GKE API and execute real operations.
- **Technical Details**:
    - SDK: `google-cloud-container` (`google.cloud.container_v1.ClusterManagerClient`).
- **Tasks**:
    - [x] Add `google-cloud-container` to `requirements.txt`.
    - [x] Implement GKE cluster creation logic in a dedicated prober class.
    - [x] Implement GKE node pool creation logic.
    - [x] Implement GKE cluster deletion logic.
    - [x] Implement operation polling to wait for cluster/nodepool transitions.
    - [x] Implement `kubectl` integration (via subprocess) for app deployment.
    - [x] Create YAML manifests for the simple app deployment.
    - [x] Implement application health validation via HTTP calls.
    - [x] Add API request/response logging for all SDK calls to state DB.
    - [x] Implement startup clean-up scan for "Daystar" labeled clusters.
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
    - [x] Create static files structure under `frontend/` (HTML, CSS, JS).
    - [x] Build the base grid layout (Rows = Time, Cols = Steps).
    - [x] Implement CSS dark theme and glassmorphism styling effects.
    - [x] Implement JS `fetch()` to pull data from FastAPI status endpoints.
    - [x] Create polling mechanism in JS for auto-refresh.
    - [x] Implement popover tooltips for displaying logs on hover.
    - [x] Add status icons (green check, red cross) based on DB values.
    - [x] Format dates and times to standard `hh:mm` format in UI.
    - [x] Add loading indicators or skeleton screens.
    - [x] Handle disconnected states gracefully with a visual indicator.
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

## Implementation Plans

The following detailed implementation plans are stored in the `plan/` directory:
- [Milestone 7 Detailed Plan](plan/implementation_plan_m7_detailed.md)
- [Automatic Cluster Creation Plan](plan/implementation_plan_auto_create.md)
- [Configuration Plan (Mock/Real)](plan/implementation_plan_config.md)
- [Original Milestone Plan](plan/implementation_plan.md)
- [Milestone 6 Plan](plan/implementation_plan_m6.md)
- [Milestone 7 Overview Plan](plan/implementation_plan_m7.md)
- [Startup Cleanup Plan](plan/implementation_plan_startup_cleanup.md)


