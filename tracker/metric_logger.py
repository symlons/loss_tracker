import time
import json
import gzip
import aiohttp
import asyncio
import threading
import queue
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict
from array import array
from itertools import islice


class RollingStats:
  """Efficient rolling statistics calculator using circular buffer"""

  def __init__(self, window_size: int = 100):
    self.window_size = window_size
    self._buffer = array("d", [0.0] * window_size)
    self._index = 0
    self._count = 0
    self._sum = 0.0

  def add(self, value: float) -> None:
    """Add a value to the rolling window"""
    if self._count < self.window_size:
      self._sum += value
      self._count += 1
    else:
      self._sum = self._sum - self._buffer[self._index] + value

    self._buffer[self._index] = value
    self._index = (self._index + 1) % self.window_size

  def mean(self) -> float:
    """Get current mean value"""
    return self._sum / self._count if self._count > 0 else 0.0


class MetricBatcher:
  """Efficient metric batching with gradual size adjustment"""

  def __init__(self, initial_size: int, min_size: int, max_size: int):
    self.current_size = initial_size
    self.min_size = min_size
    self.max_size = max_size
    self.size_multiplier = 1.2  # More gradual adjustment

    # Performance tracking
    self.processing_times = RollingStats()
    self.queue_sizes = RollingStats()

  def adjust_batch_size(self, queue_size: int, max_queue_size: int, process_time: float) -> None:
    """Gradually adjust batch size based on performance metrics"""
    self.processing_times.add(process_time)
    self.queue_sizes.add(queue_size)

    queue_pressure = queue_size / max_queue_size
    avg_process_time = self.processing_times.mean()

    if queue_pressure > 0.8 and avg_process_time < 0.01:
      # Increase batch size under pressure but processing quickly
      new_size = int(self.current_size * self.size_multiplier)
      self.current_size = min(new_size, self.max_size)
    elif queue_pressure < 0.2 and self.queue_sizes.mean() < max_queue_size * 0.3:
      # Decrease batch size when consistently under low pressure
      new_size = int(self.current_size / self.size_multiplier)
      self.current_size = max(new_size, self.min_size)


class MetricBuffer:
  """Efficient pre-allocated buffer for metric processing"""

  def __init__(self, initial_size: int = 1000):
    self.metrics = [None] * initial_size  # Initialize with None values
    self.grouped = defaultdict(list)
    self._active_indices = []

  def _resize_buffer(self, size: int) -> None:
    """Resize buffer efficiently if needed"""
    current_size = len(self.metrics)
    if current_size < size:
      # Extend the buffer to the new size
      self.metrics.extend([None] * (size - current_size))

  def ensure_capacity(self, required_size: int) -> None:
    """Ensure buffer has enough capacity"""
    if required_size > len(self.metrics):
      new_size = max(required_size, len(self.metrics) * 2)
      self._resize_buffer(new_size)

  def clear(self) -> None:
    """Clear active metrics and grouped data without full reallocation"""
    for idx in self._active_indices:
      self.metrics[idx] = None
    self._active_indices.clear()
    self.grouped.clear()


class MetricLogger:
  def __init__(
    self, metric_name: str, endpoint: Optional[str] = None, max_queue_size: int = 1000, initial_batch_size: int = 50, enable_compression: bool = False
  ):
    self.metric_name = metric_name
    self.endpoint = endpoint
    self.enable_compression = enable_compression
    self.max_queue_size = max_queue_size
    self.batch_size = initial_batch_size

    self._queue = queue.Queue(maxsize=max_queue_size)
    self._stop_flag = threading.Event()
    self._worker = None

    # Stats
    self.processed_count = 0
    self.dropped_count = 0
    self.failed_batches = 0

  def start(self):
    if self._worker is None:
      self._worker = threading.Thread(target=self._process_loop, daemon=True)
      self._worker.start()

  def log(self, step: int, value: float, metric_type: str = "loss") -> bool:
    """Log a single metric value"""
    try:
      metric = {"name": f"{self.metric_name}_{metric_type}", "xCoordinates": [step], "yCoordinates": [value]}
      self._queue.put_nowait(metric)
      return True
    except queue.Full:
      self.dropped_count += 1
      return False

  def _process_loop(self):
    while not self._stop_flag.is_set() or not self._queue.empty():
      try:
        # Process one metric at a time
        try:
          metric = self._queue.get_nowait()
        except queue.Empty:
          time.sleep(0.1)
          continue

        if self.endpoint:
          # Create new event loop for this thread
          loop = asyncio.new_event_loop()
          asyncio.set_event_loop(loop)
          try:
            loop.run_until_complete(self._send_metric(metric))
            self.processed_count += 1
          finally:
            loop.close()
        else:
          self._log_metric(metric)
          self.processed_count += 1

      except Exception as e:
        print(f"Error processing metric: {e}")
        self.failed_batches += 1

  async def _send_metric(self, metric: Dict[str, Any]) -> None:
    """Send single metric to endpoint"""
    try:
      headers = {"Content-Type": "application/json"}
      if self.enable_compression:
        headers["Content-Encoding"] = "gzip"

      data = json.dumps(metric).encode()
      if self.enable_compression:
        data = gzip.compress(data)

      async with aiohttp.ClientSession() as session:
        async with session.post(self.endpoint, data=data, headers=headers, timeout=30) as response:
          if response.status >= 400:
            print(f"Error sending metric: HTTP {response.status}")
            text = await response.text()
            print(f"Response: {text}")
            self.failed_batches += 1
          else:
            print(f"Successfully sent {metric['name']}: {metric['yCoordinates'][0]}")

    except Exception as e:
      print(f"Error sending metric: {e}")
      self.failed_batches += 1

  def _log_metric(self, metric: Dict[str, Any]) -> None:
    """Log metric locally"""
    print(f"[{self.metric_name}] Metric: {metric}")

  def get_stats(self) -> Dict[str, Any]:
    """Get current statistics"""
    return {
      "processed_count": self.processed_count,
      "dropped_count": self.dropped_count,
      "failed_batches": self.failed_batches,
      "queue_size": self._queue.qsize(),
    }

  def stop(self, timeout: float = 1.0) -> None:
    """Stop logger cleanly"""
    if self._worker and self._worker.is_alive():
      self._stop_flag.set()
      self._worker.join(timeout)


class LoggerManager:
  """Manager for multiple loggers with shared configuration"""

  def __init__(self, default_batch_size: int = 50):
    self.loggers: Dict[str, MetricLogger] = {}
    self.default_batch_size = default_batch_size

  def add_logger(
    self, name: str, metric_name: str, endpoint: Optional[str] = None, max_queue_size: int = 1000, enable_compression: bool = False
  ) -> None:
    """Add and start a new logger"""
    if name not in self.loggers:
      logger = MetricLogger(
        metric_name=metric_name,
        endpoint=endpoint,
        max_queue_size=max_queue_size,
        initial_batch_size=self.default_batch_size,
        enable_compression=enable_compression,
      )
      logger.start()
      self.loggers[name] = logger
      print(f"Logger for {metric_name} added.")
    else:
      print(f"Logger {name} already exists.")

  def log(self, logger_name: str, metrics: Dict[str, Any]) -> bool:
    """Log metrics with minimal overhead"""
    logger = self.loggers.get(logger_name)
    return logger.log(metrics) if logger else False

  def get_stats(self) -> Dict[str, Dict[str, Any]]:
    """Get performance statistics for all loggers"""
    return {name: logger.get_stats() for name, logger in self.loggers.items()}

  def stop(self, timeout: float = 1.0) -> None:
    """Stop all loggers with minimal blocking"""
    for logger in self.loggers.values():
      logger.stop(timeout)
