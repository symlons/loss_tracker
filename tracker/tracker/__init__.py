from .tracker import TrackerConfig, TrackerManager, BaseTracker, log, xy, MLTracker, BatchPriority

# Export primary classes and enums
__all__ = ["TrackerConfig", "TrackerManager", "BaseTracker", "log", "xy", "MLTracker", "BatchPriority"]

# Initialize the singleton manager
_manager = TrackerManager()

# Version info
__version__ = "1.0.0"

