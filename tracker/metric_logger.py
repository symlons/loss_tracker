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
  """Ultra high-performance metric logger for ML training"""

  def __init__(
    self, metric_name: str, endpoint: Optional[str] = None, max_queue_size: int = 1000, initial_batch_size: int = 50, enable_compression: bool = False
  ):
    self.metric_name = metric_name
    self.endpoint = endpoint
    self.enable_compression = enable_compression
    self.max_queue_size = max_queue_size

    # Efficient batching
    self.batcher = MetricBatcher(initial_size=initial_batch_size, min_size=10, max_size=max_queue_size // 2)

    # Pre-allocated buffer with initial capacity
    self.buffer = MetricBuffer(initial_batch_size)

    # Thread synchronization
    self._queue = queue.Queue(maxsize=max_queue_size)
    self._stop_flag = threading.Event()
    self._data_ready = threading.Event()
    self._worker = None

    # Async support
    self._event_loop = None
    if endpoint:
      self._event_loop = asyncio.new_event_loop()
      self._async_tasks = set()

    # Performance tracking
    self.processed_count = 0
    self.dropped_count = 0
    self.failed_batches = 0
    self.total_added = 0

  def _get_queue_size(self) -> int:
    """Get queue size with fallback for systems where qsize() is not implemented"""
    try:
      return self._queue.qsize()
    except NotImplementedError:
      return max(0, self.total_added - self.processed_count)

  def start(self) -> None:
    """Start the worker thread"""
    if self._worker is None:
      self._worker = threading.Thread(target=self._process_loop, daemon=True)
      self._worker.start()

  def log(self, metrics: Dict[str, Any]) -> bool:
    """Non-blocking log operation with minimal synchronization"""
    try:
      self._queue.put_nowait(metrics)
      self.total_added += 1
      self._data_ready.set()
      return True
    except queue.Full:
      self.dropped_count += 1
      return False

  def _process_loop(self) -> None:
    """Main processing loop optimized for throughput"""
    if self._event_loop:
      asyncio.set_event_loop(self._event_loop)

    while not self._stop_flag.is_set() or not self._queue.empty():
      batch_size = self.batcher.current_size
      start_time = time.time()

      # Process available metrics
      processed = self._process_batch(batch_size)

      if processed > 0:
        process_time = time.time() - start_time
        self.batcher.adjust_batch_size(self._get_queue_size(), self.max_queue_size, process_time)
        self._data_ready.clear()
      elif not self._stop_flag.is_set():  # Only wait if not stopping
        self._data_ready.wait(timeout=0.01)

  def _process_batch(self, batch_size: int) -> int:
    """Process a batch of metrics with minimal allocation"""
    processed = 0
    self.buffer.ensure_capacity(batch_size)  # Ensure capacity before processing
    self.buffer.clear()  # Clear previous batch data

    # Collect metrics first
    while processed < batch_size:
      try:
        metric = self._queue.get_nowait()
        if metric is not None:
          self.buffer.metrics[processed] = metric
          self.buffer._active_indices.append(processed)
          for key, value in metric.items():
            self.buffer.grouped[key].append(value)
          processed += 1
      except queue.Empty:
        break

    if processed > 0:
      grouped_metrics = dict(self.buffer.grouped)
      if self.endpoint:
        if self._event_loop:
          asyncio.run_coroutine_threadsafe(self._send_metrics_batch(grouped_metrics), self._event_loop)
      else:
        self._log_metrics_batch(grouped_metrics)

      self.processed_count += processed

    return processed

  def _compress_metrics(self, data: Dict) -> bytes:
    """Compress metrics data if enabled"""
    json_data = json.dumps(data).encode()
    return gzip.compress(json_data) if self.enable_compression else json_data

  async def _send_metrics_batch(self, grouped_metrics: Dict[str, List]) -> None:
    """Asynchronously send metrics batch to endpoint"""
    try:
      headers = {"Content-Type": "application/json"}
      if self.enable_compression:
        headers["Content-Encoding"] = "gzip"

      data = self._compress_metrics(grouped_metrics)

      async with aiohttp.ClientSession() as session:
        async with session.post(self.endpoint, data=data, headers=headers, timeout=30) as response:
          if response.status >= 400:
            self.failed_batches += 1
            print(f"Error sending metrics batch: HTTP {response.status}")
    except Exception as e:
      self.failed_batches += 1
      print(f"Error sending metrics: {e}")

  def _log_metrics_batch(self, grouped_metrics: Dict[str, List]) -> None:
    """Log metrics batch locally"""
    print(f"[{self.metric_name}] Batch metrics: {grouped_metrics}")

  def get_stats(self) -> Dict[str, Any]:
    """Get current performance statistics"""
    return {
      "processed_count": self.processed_count,
      "dropped_count": self.dropped_count,
      "failed_batches": self.failed_batches,
      "current_batch_size": self.batcher.current_size,
      "queue_size": self._get_queue_size(),
      "avg_process_time": self.batcher.processing_times.mean(),
    }

  def stop(self, timeout: float = 1.0) -> None:
    """Stop logger with minimal blocking"""
    if self._worker is not None and self._worker.is_alive():
      self._stop_flag.set()
      self._data_ready.set()  # Wake up worker
      self._worker.join(timeout)

      if self._event_loop:
        self._event_loop.stop()
        self._event_loop.close()


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
