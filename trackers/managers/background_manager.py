from concurrent.futures import ThreadPoolExecutor, Future
from queue import PriorityQueue, Empty
import threading
import time
import logging
from time import perf_counter
from typing import Optional

from ..config.tracker_config import TrackerConfig
from ..api.client import APIClient
from ..utils.metrics import MetricsCollector
from ..models import PrioritizedBatch

logger = logging.getLogger(__name__)


class BackgroundTrackerManager:
  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.batch_queue = PriorityQueue()  # Queue for batches
    self.loss_accuracy_queue = PriorityQueue()  # Queue for loss and accuracy updates
    self.metrics = MetricsCollector()
    self.stop_event = threading.Event()
    self.executor = ThreadPoolExecutor(max_workers=4)  # Handling multiple tasks in parallel
    self.api_client = APIClient(self.config)
    self.sequence_counter = 0
    self.sequence_lock = threading.Lock()
    self.background_thread = threading.Thread(target=self._background_process, daemon=self.config.daemon)
    logger.info(f"Starting background manager with config: {self.config}")
    self.background_thread.start()

  def _background_process(self):
    while not self.stop_event.is_set() or not self.batch_queue.empty():  # Keep running until we stop
      try:
        # First handle loss/accuracy updates
        if not self.loss_accuracy_queue.empty():
          loss, accuracy = self.loss_accuracy_queue.get_nowait()
          logger.info(f"Processing loss={loss:.4f}, accuracy={accuracy:.4f}")

          # Process loss and accuracy concurrently using ThreadPoolExecutor
          futures = [
            self.executor.submit(self._update_loss_tracker, loss),
            self.executor.submit(self._update_accuracy_tracker, accuracy),
          ]
          # Wait for both futures to complete
          for future in futures:
            future.result()

        # Then process batches
        if not self.batch_queue.empty():
          batch = self.batch_queue.get_nowait()
          logger.info(
            f"Got batch from queue: {batch.data['name']}, size: {len(batch.data['xCoordinates'])}, sequence: {batch.sequence_num}"
          )
          self._process_batch(batch)
        else:
          logger.debug("Batch queue is empty, waiting for new batches.")
          time.sleep(0.01)  # Sleep to avoid busy-waiting

      except Exception as e:
        logger.error(f"Error in background processing: {e}")

  def _update_loss_tracker(self, loss: float):
    # Push loss to the tracker
    logger.debug(f"Pushing loss={loss:.4f}")
    # Replace with actual tracker logic here

  def _update_accuracy_tracker(self, accuracy: float):
    # Push accuracy to the tracker
    logger.debug(f"Pushing accuracy={accuracy:.4f}")
    # Replace with actual tracker logic here

  def _process_batch(self, batch: PrioritizedBatch) -> bool:
    if not batch or not batch.data:
      logger.error("Invalid batch data received")
      return False

    start_time = perf_counter()
    try:
      logger.info(
        f"Sending batch for {batch.data['name']} with {len(batch.data['xCoordinates'])} points, sequence: {batch.sequence_num}"
      )
      success = self.api_client.send_batch(batch.data)  # Replace with actual API logic
      duration = perf_counter() - start_time
      self.metrics.add_processing_time(duration)

      if success:
        self.metrics.sent_batches += 1
        logger.info(f"Successfully sent batch for {batch.data['name']}, sequence: {batch.sequence_num}")
      else:
        self.metrics.failed_batches += 1
        logger.error(f"Failed to send batch for {batch.data['name']}, sequence: {batch.sequence_num}")

      return success
    except Exception as e:
      logger.error(f"Error processing batch: {e}")
      self.metrics.failed_batches += 1
      return False

  def queue_batch(self, batch: PrioritizedBatch):
    """Queue a batch for processing in the background."""
    batch.sequence_num = self.get_next_sequence()
    self.metrics.queued_batches += 1
    logger.info(
      f"Queueing batch for {batch.data['name']} with {len(batch.data['xCoordinates'])} points, sequence: {batch.sequence_num}"
    )
    self.batch_queue.put(batch)

  def queue_loss_accuracy(self, loss: float, accuracy: float):
    """Queue loss and accuracy values to be processed concurrently."""
    self.loss_accuracy_queue.put((loss, accuracy))

  def get_next_sequence(self) -> int:
    """Get the next sequence number in a thread-safe manner."""
    with self.sequence_lock:
      seq = self.sequence_counter
      self.sequence_counter += 1
      return seq

  def shutdown(self, wait: bool = True):
    """Shut down the background manager gracefully."""
    logger.info("Shutting down background manager")
    if wait:
      # Process any remaining batches before stopping
      while not self.batch_queue.empty():
        try:
          batch = self.batch_queue.get_nowait()
          self._process_batch(batch)
        except Empty:
          break
        except Exception as e:
          logger.error(f"Error processing remaining batch: {e}")
    self.stop_event.set()
    if wait:
      self.background_thread.join(timeout=self.config.timeout)
    self.executor.shutdown(wait=wait)
    logger.info(f"Final metrics: {self.metrics}")
