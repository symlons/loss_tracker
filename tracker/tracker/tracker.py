import requests as rq
from concurrent.futures import ThreadPoolExecutor, wait
from typing import List, Dict, Optional, Union, Any, Iterable
from queue import PriorityQueue
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrackerConfig:
  batch_size: int = 100
  max_retries: int = 3
  timeout: float = 10.0
  max_workers: int = 4
  api_host: str = "http://localhost:5005"
  use_mock_api: bool = False


class BatchPriority(Enum):
  HIGH = 1
  NORMAL = 2
  LOW = 3


@dataclass(order=True)
class PrioritizedBatch:
  priority: BatchPriority
  timestamp: float
  data: Dict = field(compare=False)


class TrackerManager:
  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
    self.failed_batches = PriorityQueue()
    self.session = rq.Session()
    self.metrics = {"sent_batches": 0, "failed_batches": 0}
    self._initialize_session()

  def _initialize_session(self):
    adapter = rq.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=self.config.max_retries)
    self.session.mount("http://", adapter)
    self.session.mount("https://", adapter)

  def send_batch(self, batch: PrioritizedBatch) -> bool:
    try:
      # No compression is applied anymore
      endpoint = f"{self.config.api_host}/batch"
      if self.config.use_mock_api:
        logger.info(f"Mock sending batch: {batch.data}")
        return True

      logger.info(f"Sending batch to {endpoint}")
      response = self.session.post(endpoint, json=batch.data, timeout=self.config.timeout)
      if response.ok:
        logger.info(f"Batch sent successfully: {response.status_code}")
        self.metrics["sent_batches"] += 1
        return True

      logger.error(f"Failed to send batch: {response.status_code} - {response.text}")
      self.metrics["failed_batches"] += 1
      return False

    except Exception as e:
      logger.error(f"Error sending batch: {e}")
      self.metrics["failed_batches"] += 1
      return False

  def retry_failed_batches(self):
    while not self.failed_batches.empty():
      try:
        batch = self.failed_batches.get_nowait()
        self.send_batch(batch)
      except Exception as e:
        logger.error(f"Error retrying batch: {e}")

  def cleanup(self):
    logger.info("Shutting down TrackerManager...")
    self.executor.shutdown(wait=True)
    self.session.close()
    logger.info("TrackerManager shutdown complete.")


class BaseTracker:
  def __init__(self, name: str, config: Optional[TrackerConfig] = None, priority: BatchPriority = BatchPriority.NORMAL):
    self.name = name
    self.config = config or TrackerConfig()
    self.manager = TrackerManager(self.config)
    self.priority = priority
    self.x_data = []
    self.y_data = []

  def push(self, x: Any, y: Any):
    self.x_data.append(x)
    self.y_data.append(y)
    # Only store data, don't flush automatically

  def flush(self):
    if not self.x_data or not self.y_data:
      return
    batch = PrioritizedBatch(
      priority=self.priority,
      timestamp=time.time(),
      data={
        "name": self.name,
        "xCoordinates": self.x_data,
        "yCoordinates": self.y_data,
      },
    )
    # Store current data and clear only after successful send
    x_data = self.x_data.copy()
    y_data = self.y_data.copy()
    batch.data["xCoordinates"] = x_data
    batch.data["yCoordinates"] = y_data
    success = self.manager.send_batch(batch)
    if success:
      self.x_data.clear()
      self.y_data.clear()

  def close(self):
    self.flush()
    self.manager.retry_failed_batches()
    self.manager.cleanup()


class XYTracker(BaseTracker):
  def __init__(
    self,
    name: str = "first",
    block_size: int = 100,
    config: Optional[TrackerConfig] = None,
    priority: BatchPriority = BatchPriority.NORMAL,
  ):
    config = config or TrackerConfig()
    config.batch_size = block_size
    super().__init__(name=name, config=config, priority=priority)

  def push(self, x: Union[Any, Iterable], y: Union[Any, Iterable]):
    if hasattr(x, "__iter__"):
      self.x_data.extend(x)
      self.y_data.extend(y)
    else:
      self.x_data.append(x)
      self.y_data.append(y)

    if len(self.x_data) >= self.config.batch_size:
      self.flush()

  def zero_track(self):
    self.x_data = [0]
    self.y_data = []


class LogTracker(BaseTracker):
  def __init__(
    self,
    name: str = "first",
    block_size: int = 2,
    config: Optional[TrackerConfig] = None,
    priority: BatchPriority = BatchPriority.NORMAL,
  ):
    config = config or TrackerConfig()
    config.batch_size = block_size
    super().__init__(name=name, config=config, priority=priority)
    self.x_count = 0
    self.zero_track()

  def push(self, y: Union[Any, Iterable]):
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

  def zero_track(self):
    self.x_data = [0]
    self.y_data = []


# Backwards compatibility classes
class xy(XYTracker):
  def __init__(self, *, name="first", block_size=100):
    config = TrackerConfig(batch_size=block_size, use_mock_api=False)
    super().__init__(name=name, block_size=block_size, config=config)
    print(self.config.api_host)


class log(LogTracker):
  def __init__(self, *, name="first", block_size=2):
    config = TrackerConfig(batch_size=block_size, use_mock_api=False)
    super().__init__(name=name, block_size=block_size, config=config)

