import logging
from tracker import MLTracker, TrackerConfig, BatchPriority, TrackerManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize TrackerManager directly to check configuration
manager = TrackerManager()
print("Initial manager config:", manager.config.__dict__)
print("Mock API status:", manager.config.mock_api)

config = TrackerConfig(mock_api=False, batch_size=2, api_host="http://localhost:5005")

# Print config before creating tracker
print("\nNew config:", config.__dict__)

tracker = MLTracker("debug_test", config=config)
print("\nTracker config:", tracker.config.__dict__)

# Test single metric
tracker.add_tracker("test", tracker_type="log")
tracker.metrics["test"].push(0.5)

# Force immediate flush
success = tracker.flush_all(timeout=2.0)
print("\nFlush success:", success)
print("Manager metrics:", tracker.metrics["test"].manager.get_metrics())

tracker.close()

