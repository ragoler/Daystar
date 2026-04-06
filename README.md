# Daystat: GKE Prober Monitoring System

Daystat is an autonomous monitoring system designed to probe the reliability and performance of Google Kubernetes Engine (GKE) by continuously executing full lifecycle operations on clusters and applications.

## Project Structure

- `backend/`: FastAPI application, manager, database, and probers.
- `frontend/`: HTML, CSS, and JS files for the UI.
- `tests/`: Unit and integration tests.
- `test_app/`: The simple application deployed to test clusters.

## Prerequisites

- Python 3.13.1 (Recommended)
- Virtual Environment (`venv`)

## Setup

1.  Initialize the virtual environment:
    ```bash
    python3 -m venv venv
    ```
2.  Activate the environment and install dependencies:
    ```bash
    source venv/bin/activate
    ./venv/bin/pip install --index-url https://pypi.org/simple -r requirements.txt
    ```

## Running the Application

1.  Start the FastAPI server:
    ```bash
    ./venv/bin/uvicorn backend.main:app --reload
    ```
2.  Access the UI at `http://localhost:8000`.

## Testing

Run all tests:
```bash
./venv/bin/pytest
```

## Deployment

### Docker

1. Build the Docker image:
   ```bash
   docker build -t daystar-app:latest .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 daystar-app:latest
   ```

### Kubernetes

1. Apply the manifests:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```
