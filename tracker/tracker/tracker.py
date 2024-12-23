import random
import time
from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue, Empty
import logging
import threading
import traceback
import requests
from typing import Optional
from collections import Counter
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchPriority(Enum):
  HIGH = 1
  NORMAL = 2
  LOW = 3


@dataclass(order=True)
class PrioritizedBatch:
  priority: BatchPriority
  timestamp: float
  data: dict = field(compare=False)
  retry_count: int = field(default=0, compare=False)


@dataclass
class TrackerConfig:
  batch_size: int = 100
  max_retries: int = 3
  timeout: float = 10.0
  max_workers: int = 4
  api_host: str = "http://localhost:5005/batch"
  use_mock_api: bool = False
  daemon: bool = True


class BackgroundTrackerManager:
  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.batch_queue = PriorityQueue()
    self.metrics = Counter()
    self.stop_event = threading.Event()
    self.background_thread = threading.Thread(target=self._background_process, daemon=self.config.daemon)
    self.background_thread.start()

  def _background_process(self):
    while not self.stop_event.is_set():
      try:
        batch = self.batch_queue.get(timeout=1)
        success = self._process_batch(batch)
        if success:
          logger.debug(f"Successfully processed batch: {batch}")
          self.metrics["sent_batches"] += 1
        else:
          logger.error(f"Failed to process batch: {batch}")
          self.metrics["failed_batches"] += 1
        self.batch_queue.task_done()
      except Empty:
        continue
      except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())

  def _process_batch(self, batch: PrioritizedBatch):
    try:
      if self.config.use_mock_api:
        logger.info("Simulating API request...")
        return True

      url = self.config.api_host
      retries = 0

      while retries < self.config.max_retries:
        try:
          response = requests.post(url, json=batch.data, timeout=self.config.timeout)
          if response.status_code == 200:
            logger.info(f"Batch successfully sent: {response.status_code}")
            return True
          else:
            logger.warning(f"Backend returned error: {response.status_code}")
        except requests.exceptions.RequestException as e:
          logger.warning(f"Retrying due to error: {e}")

        retries += 1
        backoff_time = (2**retries) + random.uniform(0, 1)
        time.sleep(backoff_time)

      logger.error("Max retries exceeded for batch.")
      return False
    except Exception as e:
      logger.error(f"Error processing batch: {e}")
      return False

  def queue_batch(self, batch: PrioritizedBatch):
    self.metrics["queued_batches"] += 1
    self.batch_queue.put(batch)

  def shutdown(self, wait=True):
    self.stop_event.set()
    if wait:
      self.background_thread.join(timeout=self.config.timeout)
    logger.info(f"Final metrics: {dict(self.metrics)}")


class BaseTracker:
  def __init__(self, name: str, config: Optional[TrackerConfig] = None, priority: BatchPriority = BatchPriority.NORMAL):
    self.name = name
    self.config = config or TrackerConfig()
    self.manager = BackgroundTrackerManager(self.config)
    self.priority = priority
    self._reset_data()

  def _reset_data(self):
    self.x_data = []
    self.y_data = []

  def push(self, x: any, y: any):
    self.x_data.append(x)
    self.y_data.append(y)
    if len(self.x_data) >= self.config.batch_size:
      self.flush()

  def flush(self):
    if not self.x_data or not self.y_data:
      return

    batch = PrioritizedBatch(
      priority=self.priority,
      timestamp=time.time(),
      data={
        "name": self.name,
        "xCoordinates": self.x_data.copy(),
        "yCoordinates": self.y_data.copy(),
      },
    )
    self.manager.queue_batch(batch)
    self._reset_data()

  def close(self):
    self.flush()
    while self.manager.batch_queue.qsize() > 0:
      logger.info(f"Waiting for {self.name} batches... (Remaining: {self.manager.batch_queue.qsize()})")
      time.sleep(1)
    self.manager.shutdown(wait=True)


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

  def push(self, x: any, y: any):
    if not hasattr(x, "__iter__"):
      x, y = [x], [y]
    if len(x) != len(y):
      raise ValueError("x and y must have the same length")
    self.x_data.extend(x)
    self.y_data.extend(y)
    if len(self.x_data) >= self.config.batch_size:
      self.flush()


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
    self._reset_data()

  def push(self, y: any):
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


# Convenience aliases for backward compatibility
class xy(XYTracker):
  def __init__(self, *, name="first", block_size=100):
    super().__init__(name=name, block_size=block_size)


class log(LogTracker):
  def __init__(self, *, name="first", block_size=2):
    super().__init__(name=name, block_size=block_size)


# This will simulate the training step, adding some noise to the loss and accuracy
def train_step(epoch):
  base_loss = max(0.1, 1.0 - (epoch * 0.01))
  noise = random.gauss(0, 0.05)
  loss = base_loss + noise
  accuracy = min(1.0, 0.5 + (epoch * 0.005))
  accuracy_noise = random.gauss(0, 0.02)
  accuracy += accuracy_noise
  return loss, accuracy


def training_loop(num_epochs=1000):
  loss_tracker = xy(name="training_loss")
  accuracy_tracker = xy(name="training_accuracy")

  print("Starting training loop...")
  start_time = time.time()

  for epoch in tqdm(range(num_epochs), desc="Training Progress"):
    loss, accuracy = train_step(epoch)
    loss_tracker.push(epoch, loss)
    accuracy_tracker.push(epoch, accuracy)
    if epoch % 10 == 0:
      logger.info(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")

  loss_tracker.close()
  accuracy_tracker.close()

  end_time = time.time()
  print(f"\nTraining completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
  training_loop()
