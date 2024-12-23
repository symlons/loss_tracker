from abc import ABC, abstractmethod
from typing import Any, List, Optional
import time

from ..config.tracker_config import TrackerConfig
from ..models import BatchPriority, PrioritizedBatch
from ..managers.background_manager import BackgroundTrackerManager


class BaseTracker(ABC):
  """Abstract base class for all trackers."""

  def __init__(self, name: str, config: Optional[TrackerConfig] = None, priority: BatchPriority = BatchPriority.NORMAL):
    self.name = name
    self.config = config or TrackerConfig()
    self.manager = BackgroundTrackerManager(self.config)
    self.priority = priority
    self._sequence_counter = 0
    self._reset_data()

  def _reset_data(self):
    self.x_data: List[Any] = []
    self.y_data: List[Any] = []

  @abstractmethod
  def push(self, x: Any, y: Any):
    """Push data points to the tracker."""
    pass

  def flush(self):
    """Flush current data to the manager."""
    if not self.x_data or not self.y_data:
      return

    batch = PrioritizedBatch(
      priority=self.priority,
      sequence_num=self._sequence_counter,
      data={
        "name": self.name,
        "xCoordinates": self.x_data.copy(),
        "yCoordinates": self.y_data.copy(),
      },
    )
    self._sequence_counter += 1
    self.manager.queue_batch(batch)
    self._reset_data()

  def close(self):
    """Close the tracker and ensure all data is sent."""
    self.flush()
    self.manager.shutdown(wait=True)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

