from typing import Any, List, Optional, Union
from ..config.tracker_config import TrackerConfig
from ..models import BatchPriority
from .base import BaseTracker


class XYTracker(BaseTracker):
  """Tracker for x-y coordinate data."""

  def __init__(
    self,
    name: str = "first",
    block_size: int = 100,
    config: Optional[TrackerConfig] = None,
    priority: BatchPriority = BatchPriority.NORMAL,
  ):
    # Create a new config with the specified block_size instead of modifying the existing one
    config_dict = config.__dict__ if config else {}
    config = TrackerConfig(batch_size=block_size, **{k: v for k, v in config_dict.items() if k != "batch_size"})
    super().__init__(name=name, config=config, priority=priority)

  def push(self, x: Union[Any, List[Any]], y: Union[Any, List[Any]]):
    """Push x-y coordinate data to the tracker."""
    if not hasattr(x, "__iter__"):
      x, y = [x], [y]
    if len(x) != len(y):
      raise ValueError("x and y must have the same length")
    self.x_data.extend(x)
    self.y_data.extend(y)
    if len(self.x_data) >= self.config.batch_size:
      self.flush()


# Convenience alias
xy = XYTracker

