import asyncio
import datetime
import logging
import os
import time
from typing import List, Optional
import yaml
from pydantic import BaseModel
from backend.database import init_cluster, update_cluster_step, log_api_call, get_active_clusters, ClusterState
from backend.probers import MockProber, ProberResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEDULE_PATH = os.environ.get("SCHEDULE_PATH", "data/schedule.yaml")
SAFETY_LIMIT = 15 # As approved by user

class ScheduleItem(BaseModel):
    minute: int
    step: str

class Schedule(BaseModel):
    schedule: List[ScheduleItem]

def load_schedule(path: str = SCHEDULE_PATH) -> Schedule:
    """Load schedule from YAML file."""
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            return Schedule(**data)
    except Exception as e:
        logger.error(f"Failed to load schedule from {path}: {e}")
        # Return a default schedule if failed or file missing
        return Schedule(schedule=[
            ScheduleItem(minute=1, step="create_cluster"),
            ScheduleItem(minute=15, step="delete_cluster")
        ])

def get_step_for_minute(schedule: Schedule, minute: int) -> Optional[str]:
    """Get the step scheduled for a specific minute."""
    for item in schedule.schedule:
        if item.minute == minute:
            return item.step
    return None

def cleanup_resources():
    """Cleanup all resources (mock files)."""
    mock_dir = "data/mock_resources"
    if os.path.exists(mock_dir):
        for f in os.listdir(mock_dir):
            os.remove(os.path.join(mock_dir, f))
    logger.info("Cleaned up mock resources.")

async def process_tick(schedule: Schedule, current_time: datetime.datetime = None):
    """Process a single tick (minute) for all clusters."""
    start_time = time.time()
    if current_time is None:
        current_time = datetime.datetime.now()
        
    logger.info(f"Processing tick at {current_time.isoformat()}")
    
    # Automatically initialize a new cluster on every tick
    cluster_name = f"daystar-{int(time.time())}"
    init_cluster(cluster_name)
    logger.info(f"Automatically initialized new cluster: {cluster_name}")
    
    clusters = get_active_clusters()
    
    # Safety Check
    if len(clusters) > SAFETY_LIMIT:
        logger.warning(f"Safety limit exceeded ({len(clusters)} > {SAFETY_LIMIT}). Triggering cleanup.")
        cleanup_resources()
        from backend.database import clusters_table
        clusters_table.truncate()
        logger.info("Purged clusters table.")
        duration = time.time() - start_time
        logger.info(f"process_tick took {duration:.4f} seconds (safety limit triggered)")
        return
        
    for cluster in clusters:
        # Calculate elapsed minutes
        created_at = datetime.datetime.fromisoformat(cluster.created_at)
        elapsed = current_time - created_at
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        logger.info(f"Cluster {cluster.name}: elapsed minutes = {elapsed_minutes}")
        
        step = get_step_for_minute(schedule, elapsed_minutes)
        if step:
            logger.info(f"Executing step {step} for cluster {cluster.name}")
            
            # Call Prober
            # For now we use MockProber
            prober = MockProber()
            result = prober.execute(cluster.name)
            
            # Update DB
            update_cluster_step(
                cluster.name,
                step,
                "success" if result.success else "failed",
                result.logs
            )
            
    duration = time.time() - start_time
    logger.info(f"process_tick took {duration:.4f} seconds")

async def main_loop():
    """Main scheduling loop."""
    schedule = load_schedule()
    logger.info(f"Loaded schedule: {schedule}")
    
    while True:
        await process_tick(schedule, datetime.datetime.now())
        # Sleep for 60 seconds
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())
