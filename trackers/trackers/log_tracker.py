from typing import Any, List, Optional, Union
from ..config.tracker_config import TrackerConfig
from ..models import BatchPriority
from .base import BaseTracker


class LogTracker(BaseTracker):
  """Tracker for sequential logging data."""

  def __init__(
    self,
    name: str = "first",
    block_size: int = 2,
    config: Optional[TrackerConfig] = None,
    priority: BatchPriority = BatchPriority.NORMAL,
  ):
    # Create a new config with the specified block_size
    config_dict = config.__dict__ if config else {}
    config = TrackerConfig(batch_size=block_size, **{k: v for k, v in config_dict.items() if k != "batch_size"})
    super().__init__(name=name, config=config, priority=priority)
    self.x_count = 0

  def push(self, y: Union[Any, List[Any]]):
    """Push sequential data points to the tracker."""
    if hasattr(y, "__iter__"):
      last_x = self.x_data[-1] if self.x_data else 0
      self.x_data.extend(range(last_x + 1, last_x + len(y) + 1))
      self.y_data.extend(y)
    else:
      self.x_data.append(self.x_count)
      self.y_data.append(y)
      self.x_count += 1
    if len(self.y_data) >= self.config.batch_size:
      self.flush()


# Convenience alias
log = LogTracker

