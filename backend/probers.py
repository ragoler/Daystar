from abc import ABC, abstractmethod
from pydantic import BaseModel
import time
import random
import os

class ProberResult(BaseModel):
    success: bool
    logs: str
    latency: float

class BaseProber(ABC):
    @abstractmethod
    def execute(self, resource_name: str) -> ProberResult:
        """Executes the prober action."""
        pass

    @abstractmethod
    def get_logs(self) -> str:
        """Returns the logs from the last execution."""
        pass

class MockProber(BaseProber):
    def __init__(self, failure_rate: float = 0.1, sleep_delay: float = 1.0, data_dir: str = "data/mock_resources"):
        self.failure_rate = failure_rate
        self.sleep_delay = sleep_delay
        self.data_dir = data_dir
        self.logs = ""
        
        # Ensure data dir exists
        os.makedirs(self.data_dir, exist_ok=True)

    def execute(self, resource_name: str) -> ProberResult:
        self.logs = f"Starting mock execution for {resource_name}\n"
        start_time = time.time()
        
        # Simulate latency
        self.logs += f"Simulating latency: sleeping for {self.sleep_delay}s\n"
        time.sleep(self.sleep_delay)
        
        # Simulate file creation
        file_path = os.path.join(self.data_dir, f"{resource_name}.mock")
        self.logs += f"Simulating file creation at {file_path}\n"
        try:
            with open(file_path, "w") as f:
                f.write(f"Mock resource for {resource_name}")
        except Exception as e:
            self.logs += f"Failed to create file: {e}\n"
            latency = time.time() - start_time
            return ProberResult(success=False, logs=self.logs, latency=latency)

        # Random failure injection
        if random.random() < self.failure_rate:
            self.logs += "Random failure injected!\n"
            latency = time.time() - start_time
            # Clean up on failure to simulate failed creation? Or leave it?
            # Let's leave it to simulate resource leakage if that's what we want to test,
            # or clean it up. The plan says "Initialization: On application startup, the system will identify and purge all existing resources with the Daystar label".
            # For now let's just leave it or delete it. Let's delete it to be clean if it failed.
            if os.path.exists(file_path):
                os.remove(file_path)
            return ProberResult(success=False, logs=self.logs, latency=latency)
        
        self.logs += f"Mock execution for {resource_name} succeeded\n"
        latency = time.time() - start_time
        return ProberResult(success=True, logs=self.logs, latency=latency)

    def get_logs(self) -> str:
        return self.logs
