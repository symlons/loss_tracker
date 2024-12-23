import asyncio
from typing import Optional, List
import logging
from time import perf_counter

from ..config.tracker_config import TrackerConfig
from ..models import PrioritizedBatch
from ..api.async_client import AsyncAPIClient
from ..utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class AsyncBackgroundTrackerManager:
  """Asynchronous version of the background tracker manager."""

  def __init__(self, config: Optional[TrackerConfig] = None):
    self.config = config or TrackerConfig()
    self.metrics = MetricsCollector()
    self.queue = asyncio.Queue()
    self.stop_event = asyncio.Event()
    self.api_client = AsyncAPIClient(self.config)
    self.tasks: List[asyncio.Task] = []

  async def start(self):
    """Start the background processing tasks."""
    for _ in range(self.config.max_workers):
      task = asyncio.create_task(self._background_process())
      self.tasks.append(task)

  async def _background_process(self):
    while not self.stop_event.is_set():
      try:
        batch = await self.queue.get()
        await self._process_batch(batch)
        self.queue.task_done()
      except Exception as e:
        logger.error(f"Async batch processing error: {e}")

  async def _process_batch(self, batch: PrioritizedBatch) -> bool:
    if not batch or not batch.data:
      logger.error("Invalid batch data received")
      return False

    start_time = perf_counter()
    try:
      success = await self.api_client.send_batch(batch.data)
      self.metrics.add_processing_time(perf_counter() - start_time)

      if success:
        self.metrics.sent_batches += 1
      else:
        self.metrics.failed_batches += 1

      return success
    except Exception as e:
      logger.error(f"Error processing batch: {e}")
      self.metrics.failed_batches += 1
      return False

  async def queue_batch(self, batch: PrioritizedBatch):
    self.metrics.queued_batches += 1
    await self.queue.put(batch)

  async def shutdown(self):
    """Shutdown the manager and wait for all tasks to complete."""
    self.stop_event.set()
    await self.queue.join()
    for task in self.tasks:
      task.cancel()
    await asyncio.gather(*self.tasks, return_exceptions=True)
    logger.info(f"Final metrics: {self.metrics}")
