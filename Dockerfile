FROM google/cloud-sdk:slim

# Install kubectl
RUN gcloud components install kubectl

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directory and copy schedule
RUN mkdir -p data
COPY data/schedule.yaml ./data/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
