from trackers.trackers import log
from trackers.config.tracker_config import TrackerConfig

tracker = log(name="example_log", config=TrackerConfig(batch_size=2))

tracker.push([10, 20, 30, 40])
