import random
import time
from enum import Enum
from dataclasses import dataclass, field
from queue import Queue, Empty
import logging
import threading
import traceback
import requests
from typing import Optional


# Configure logging for the library
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


class TrackerConfig:
  batch_size: int = 100
  max_retries: int = 3  # Max retries before failing
  timeout: float = 10.0  # Timeout for each request
  max_workers: int = 4
  api_host: str = "http://localhost:5005/batch"  # Corrected to batch endpoint
  use_mock_api: bool = False  # Flag to switch between mock and actual API
  daemon: bool = True  # Background thread as daemon by default


class BackgroundTrackerManager:
  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.batch_queue = Queue()
    self.metrics = {"sent_batches": 0, "failed_batches": 0, "queued_batches": 0}
    self.stop_event = threading.Event()
    self.background_thread = threading.Thread(target=self._background_process, daemon=self.config.daemon)
    self.background_thread.start()

  def _background_process(self):
    while not self.stop_event.is_set():
      try:
        batch = self.batch_queue.get(timeout=1)  # Wait for a new batch or timeout
        # logger.debug(f"Processing batch: {batch}")  # Log the batch being processed

        # Simulate sending the batch (replace with actual logic)
        success = self._process_batch(batch)
        if success:
          logger.debug(f"Successfully processed batch: {batch}")
          self.metrics["sent_batches"] += 1
        else:
          logger.error(f"Failed to process batch: {batch}")
          self.metrics["failed_batches"] += 1

        self.batch_queue.task_done()

      except Empty:
        continue  # Timeout occurred, continue checking for new batches

      except Exception as e:
        logger.error(f"Error processing batch: {e}")
        logger.error(traceback.format_exc())

  def _process_batch(self, batch: PrioritizedBatch):
    """
    This function processes a batch, e.g., by sending it to a backend API.
    For now, it simulates a request.
    """
    try:
      # logger.info(f"Processing batch: {batch.data}")

      # Simulate sending data to the backend via a POST request
      if self.config.use_mock_api:
        logger.info("Simulating API request...")
        return True  # Mock success
      else:
        # Actual API call - send data to the backend
        url = self.config.api_host
        retries = batch.retry_count

        while retries < self.config.max_retries:
          try:
            response = requests.post(url, json=batch.data, timeout=self.config.timeout)
            if response.status_code == 200:
              logger.info(f"Successfully sent batch to backend: {response.status_code}")
              return True
            else:
              logger.error(f"Failed to send batch to backend, status code: {response.status_code}")
              retries += 1
              time.sleep(2)  # Wait before retrying
          except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            retries += 1
            time.sleep(2)  # Wait before retrying

        logger.error(f"Batch failed after {self.config.max_retries} retries.")
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
    logger.info(f"Final metrics: {self.metrics}")


class BaseTracker:
  def __init__(self, name: str, config: Optional[TrackerConfig] = None, priority: BatchPriority = BatchPriority.NORMAL):
    self.name = name
    self.config = config or TrackerConfig()
    self.manager = BackgroundTrackerManager(self.config)
    self.priority = priority
    self.x_data = []
    self.y_data = []

  def push(self, x: any, y: any):
    """
    Push data point with minimal overhead.
    Automatically flushes when batch size is reached.
    """
    self.x_data.append(x)
    self.y_data.append(y)

    # Auto-flush when batch size is reached
    if len(self.x_data) >= self.config.batch_size:
      self.flush()

  def flush(self):
    """
    Flush accumulated data as a batch.
    Returns immediately, processing happens in background.
    """
    if not self.x_data or not self.y_data:
      return

    # Create a prioritized batch
    batch = PrioritizedBatch(
      priority=self.priority,
      timestamp=time.time(),
      data={
        "name": self.name,
        "xCoordinates": self.x_data.copy(),
        "yCoordinates": self.y_data.copy(),
      },
    )

    # Queue batch for background processing
    self.manager.queue_batch(batch)

    # Clear the data after queuing
    self.x_data.clear()
    self.y_data.clear()

  def close(self):
    """
    Flush any remaining data and shutdown the background processing.
    """
    # Flush any remaining data
    self.flush()

    # Shutdown the background manager
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
    """
    Push multiple data points or single point.
    Supports both single and iterable inputs.
    """
    if hasattr(x, "__iter__"):
      self.x_data.extend(x)
      self.y_data.extend(y)
    else:
      self.x_data.append(x)
      self.y_data.append(y)

    # Auto-flush when batch size is reached
    if len(self.x_data) >= self.config.batch_size:
      self.flush()

  def zero_track(self):
    """Reset tracking to zero."""
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

  def push(self, y: any):
    """
    Push logarithmic tracking data points.
    Automatically assigns x-coordinates.
    """
    if hasattr(y, "__iter__"):
      last_x = self.x_data[-1] if self.x_data else 0
      self.x_data.extend(range(last_x + 1, last_x + len(y) + 1))
      self.y_data.extend(y)
    else:
      self.x_data.append(self.x_count)
      self.y_data.append(y)
      self.x_count += 1

    # Auto-flush when batch size is reached
    if len(self.y_data) >= self.config.batch_size:
      self.flush()

  def zero_track(self):
    """Reset tracking to zero."""
    self.x_data = [0]
    self.y_data = []


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


def training_loop():
  # Create trackers for loss and accuracy
  loss_tracker = xy(name="training_loss")
  accuracy_tracker = xy(name="training_accuracy")

  num_epochs = 1000  # Number of epochs for training
  print("Starting training loop...")
  start_time = time.time()

  # Iterate over epochs
  for epoch in range(num_epochs):
    loss, accuracy = train_step(epoch)  # Generate loss and accuracy for the current epoch

    # Push the data points to the trackers (loss and accuracy)
    loss_tracker.push(epoch, loss)
    accuracy_tracker.push(epoch, accuracy)

    # Print training progress every 10 epochs
    if epoch % 10 == 0:
      print(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")

  # Close trackers to flush remaining data and process all batches
  loss_tracker.close()
  accuracy_tracker.close()

  end_time = time.time()
  print(f"\nTraining completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
  training_loop()
