from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue, Empty
import threading
from typing import Optional, Dict
from time import perf_counter
import logging
import time
from collections import OrderedDict

from ..config.tracker_config import TrackerConfig
from ..models import PrioritizedBatch
from ..api.client import APIClient
from ..utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class BackgroundTrackerManager:
  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.batch_queue = PriorityQueue()
    self.metrics = MetricsCollector()
    self.stop_event = threading.Event()
    self.executor = ThreadPoolExecutor(max_workers=1)  # Force single worker
    self.api_client = APIClient(self.config)
    self.sequence_counter = 0
    self.sequence_lock = threading.Lock()
    self.background_thread = threading.Thread(target=self._background_process, daemon=self.config.daemon)
    logger.info(f"Starting background manager with config: {self.config}")
    self.background_thread.start()

  def _background_process(self):
    while not self.stop_event.is_set() or not self.batch_queue.empty():  # Changed condition
      try:
        batch = self.batch_queue.get_nowait()
        logger.info(
          f"Got batch from queue: {batch.data['name']}, size: {len(batch.data['xCoordinates'])}, sequence: {batch.sequence_num}"
        )
        # Process synchronously
        self._process_batch(batch)
      except Empty:
        time.sleep(0.01)
      except Exception as e:
        logger.error(f"Batch processing error: {e}")

  def _process_batch(self, batch: PrioritizedBatch) -> bool:
    if not batch or not batch.data:
      logger.error("Invalid batch data received")
      return False

    start_time = perf_counter()
    try:
      logger.info(
        f"Sending batch for {batch.data['name']} with {len(batch.data['xCoordinates'])} points, sequence: {batch.sequence_num}"
      )
      success = self.api_client.send_batch(batch.data)
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

  def get_next_sequence(self) -> int:
    """Get next sequence number thread-safely."""
    with self.sequence_lock:
      seq = self.sequence_counter
      self.sequence_counter += 1
      return seq

  def queue_batch(self, batch: PrioritizedBatch):
    """Queue a batch with a globally ordered sequence number."""
    batch.sequence_num = self.get_next_sequence()
    self.metrics.queued_batches += 1
    logger.info(
      f"Queueing batch for {batch.data['name']} with {len(batch.data['xCoordinates'])} points, sequence: {batch.sequence_num}"
    )
    self.batch_queue.put(batch)

  def shutdown(self, wait: bool = True):
    logger.info("Shutting down background manager")
    if wait:
      # Process remaining items in queue before stopping
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

