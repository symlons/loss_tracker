# metric_logger.py

import asyncio
import aiohttp
import time
import json
import gzip
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
from array import array
from itertools import islice
import threading
import queue


class LoggerMode(Enum):
  TRAINING = "training"
  POST_TRAINING = "post_training"


@dataclass
class MetricConfig:
  """Configuration for metric collection"""

  name: str
  endpoint: Optional[str] = None
  max_queue_size: int = 1000
  batch_size: int = 50
  retry_attempts: int = 3
  retry_delay: float = 0.5
  enable_compression: bool = False


class RollingStats:
  """Efficient rolling statistics calculator using circular buffer"""

  def __init__(self, window_size: int = 100):
    self.window_size = window_size
    self._buffer = array("d", [0.0] * window_size)
    self._index = 0
    self._count = 0
    self._sum = 0.0
    self._min = float("inf")
    self._max = float("-inf")

  def add(self, value: float) -> None:
    if self._count < self.window_size:
      self._sum += value
      self._count += 1
    else:
      old_value = self._buffer[self._index]
      self._sum = self._sum - old_value + value

    self._buffer[self._index] = value
    self._index = (self._index + 1) % self.window_size

    self._min = min(self._min, value)
    self._max = max(self._max, value)

  def mean(self) -> float:
    return self._sum / self._count if self._count > 0 else 0.0

  def min(self) -> float:
    return self._min if self._count > 0 else 0.0

  def max(self) -> float:
    return self._max if self._count > 0 else 0.0


class MetricBatcher:
  """Efficient metric batching with gradual size adjustment"""

  def __init__(self, initial_size: int, min_size: int, max_size: int):
    self.current_size = initial_size
    self.min_size = min_size
    self.max_size = max_size
    self.size_multiplier = 1.2

    self.processing_times = RollingStats()
    self.queue_sizes = RollingStats()

  def adjust_batch_size(self, queue_size: int, max_queue_size: int, process_time: float) -> None:
    """Gradually adjust batch size based on performance metrics"""
    self.processing_times.add(process_time)
    self.queue_sizes.add(queue_size)

    queue_pressure = queue_size / max_queue_size
    avg_process_time = self.processing_times.mean()

    if queue_pressure > 0.8 and avg_process_time < 0.01:
      new_size = int(self.current_size * self.size_multiplier)
      self.current_size = min(new_size, self.max_size)
    elif queue_pressure < 0.2 and self.queue_sizes.mean() < max_queue_size * 0.3:
      new_size = int(self.current_size / self.size_multiplier)
      self.current_size = max(new_size, self.min_size)


class MetricBuffer:
  """Efficient pre-allocated buffer for metric processing"""

  def __init__(self, initial_size: int = 1000):
    self.metrics = [None] * initial_size
    self.grouped = defaultdict(list)
    self._active_indices = []

  def _resize_buffer(self, size: int) -> None:
    """Resize buffer efficiently if needed"""
    current_size = len(self.metrics)
    if current_size < size:
      self.metrics.extend([None] * (size - current_size))

  def ensure_capacity(self, required_size: int) -> None:
    """Ensure buffer has enough capacity"""
    if required_size > len(self.metrics):
      new_size = max(required_size, len(self.metrics) * 2)
      self._resize_buffer(new_size)

  def clear(self) -> None:
    """Clear active metrics and grouped data"""
    for idx in self._active_indices:
      self.metrics[idx] = None
    self._active_indices.clear()
    self.grouped.clear()

  def add(self, metric: Dict[str, Any]) -> None:
    """Add metric to buffer"""
    if len(self._active_indices) >= len(self.metrics):
      self.ensure_capacity(len(self.metrics) * 2)

    idx = len(self._active_indices)
    self.metrics[idx] = metric
    self._active_indices.append(idx)

  def get_metrics(self) -> List[Dict[str, Any]]:
    """Get all active metrics"""
    return [self.metrics[idx] for idx in self._active_indices]


class AdaptiveInterval:
  """Manages adaptive flush intervals based on system load"""

  def __init__(self):
    self.min_interval = 2.0  # Minimum interval under heavy load
    self.max_interval = 30.0  # Maximum interval when quiet
    self.normal_interval = 12.0  # Target interval during normal training
    self.post_training_interval = 1.0  # Post-training interval

    self.load_stats = RollingStats(20)
    self.pressure_threshold_high = 0.8
    self.pressure_threshold_low = 0.2

  def get_interval(self, mode: LoggerMode, queue_pressure: float) -> float:
    """Calculate appropriate interval based on mode and system load"""
    if mode == LoggerMode.POST_TRAINING:
      return self.post_training_interval

    self.load_stats.add(queue_pressure)
    avg_load = self.load_stats.mean()

    if avg_load > self.pressure_threshold_high:
      return self.min_interval
    elif avg_load < self.pressure_threshold_low:
      return min(self.max_interval, self.normal_interval * 1.5)
    else:
      load_factor = (avg_load - self.pressure_threshold_low) / (self.pressure_threshold_high - self.pressure_threshold_low)
      return self.normal_interval + (self.min_interval - self.normal_interval) * load_factor


class MetricLogger:
  """Advanced metric logger with adaptive batching and dual-mode operation"""

  def __init__(self, config: MetricConfig):
    self.config = config
    self._queue = asyncio.Queue(maxsize=config.max_queue_size)
    self._stop_event = asyncio.Event()
    self.mode = LoggerMode.TRAINING

    # Adaptive components
    self.adaptive_interval = AdaptiveInterval()
    self._buffer = MetricBuffer(config.batch_size * 2)
    self._batcher = MetricBatcher(initial_size=config.batch_size, min_size=max(10, config.batch_size // 2), max_size=min(200, config.batch_size * 2))

    # Performance tracking
    self.metrics = {
      "processed_count": 0,
      "dropped_count": 0,
      "failed_batches": 0,
      "retried_batches": 0,
      "batch_processing_times": RollingStats(100),
      "queue_pressure": RollingStats(100),
      "batch_sizes": RollingStats(100),
    }

    # Start processing task
    self._process_task = asyncio.create_task(self._process_metrics())
    self._last_flush_time = time.monotonic()

  async def log(self, step: float, value: float, metric_type: str) -> bool:
    """Log a metric value"""
    if self._stop_event.is_set():
      return False

    try:
      metric = {
        "name": f"{self.config.name}_{metric_type}",
        "step": float(step),  # Ensure numeric
        "value": float(value),  # Ensure numeric
      }

      # Adjust timeout based on mode
      timeout = 0.1 if self.mode == LoggerMode.POST_TRAINING else 0.001

      try:
        await asyncio.wait_for(self._queue.put(metric), timeout=timeout)
        return True
      except (asyncio.QueueFull, asyncio.TimeoutError):
        self.metrics["dropped_count"] += 1
        return False

    except Exception as e:
      print(f"Logging error: {e}")
      return False

  async def _process_metrics(self) -> None:
    """Main metric processing loop"""
    async with aiohttp.ClientSession() as session:
      while not self._stop_event.is_set() or not self._queue.empty():
        batch_start = time.monotonic()

        # Get current adaptive interval
        current_interval = self.adaptive_interval.get_interval(self.mode, self._queue.qsize() / self._queue.maxsize)

        try:
          # Collect batch
          batch = []
          desired_batch_size = self._batcher.current_size

          while len(batch) < desired_batch_size:
            try:
              time_since_flush = time.monotonic() - self._last_flush_time
              timeout = max(0.001, current_interval - time_since_flush)

              metric = await asyncio.wait_for(self._queue.get(), timeout=timeout)
              batch.append(metric)
              self._queue.task_done()
            except asyncio.TimeoutError:
              break

          # Process batch if not empty
          if batch:
            self._buffer.clear()
            for metric in batch:
              self._buffer.add(metric)

            await self._send_batch(session, self._buffer.get_metrics())
            self._last_flush_time = time.monotonic()

            # Update batch size based on performance
            batch_time = time.monotonic() - batch_start
            self._batcher.adjust_batch_size(self._queue.qsize(), self._queue.maxsize, batch_time)

          # Update metrics
          batch_time = time.monotonic() - batch_start
          self.metrics["batch_processing_times"].add(batch_time)
          self.metrics["queue_pressure"].add(self._queue.qsize() / self._queue.maxsize)
          self.metrics["batch_sizes"].add(len(batch))

        except Exception as e:
          print(f"Processing error: {e}")
          await asyncio.sleep(0.1)

  async def _send_batch(self, session: aiohttp.ClientSession, batch: List[Dict]) -> None:
    """Send a batch of metrics with retries"""
    if not self.config.endpoint:
      return

    # Group metrics by name
    grouped = defaultdict(lambda: {"xCoordinates": [], "yCoordinates": []})
    for metric in batch:
      name = metric["name"]
      grouped[name]["xCoordinates"].append(metric["step"])
      grouped[name]["yCoordinates"].append(metric["value"])

    # Process each group
    for name, data in grouped.items():
      payload = {"name": name, "xCoordinates": [float(x) for x in data["xCoordinates"]], "yCoordinates": [float(y) for y in data["yCoordinates"]]}

      # Compression if enabled
      headers = {"Content-Type": "application/json"}
      if self.config.enable_compression:
        payload_bytes = json.dumps(payload).encode("utf-8")
        payload = gzip.compress(payload_bytes)
        headers["Content-Encoding"] = "gzip"

      # Send with retries
      for attempt in range(self.config.retry_attempts):
        try:
          async with session.post(
            self.config.endpoint,
            json=payload if not self.config.enable_compression else None,
            data=payload if self.config.enable_compression else None,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=1),
          ) as response:
            if response.status < 400:
              self.metrics["processed_count"] += len(data["xCoordinates"])
              break
            else:
              print(f"Failed to send metrics: HTTP {response.status}")
              if attempt < self.config.retry_attempts - 1:
                self.metrics["retried_batches"] += 1
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
              else:
                self.metrics["failed_batches"] += 1

        except Exception as e:
          print(f"Error sending batch (attempt {attempt + 1}): {e}")
          if attempt < self.config.retry_attempts - 1:
            self.metrics["retried_batches"] += 1
            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
          else:
            self.metrics["failed_batches"] += 1

  def set_mode(self, mode: LoggerMode) -> None:
    """Switch between training and post-training modes"""
    self.mode = mode
    print(f"Switched to {mode.value} mode")

  async def stop(self, timeout: float = 5.0) -> None:
    """Stop processing with graceful shutdown"""
    self.set_mode(LoggerMode.POST_TRAINING)
    self._stop_event.set()

    try:
      await asyncio.wait_for(self._process_task, timeout=timeout)
    except asyncio.TimeoutError:
      print("Processing did not complete within timeout")
    finally:
      if not self._process_task.done():
        self._process_task.cancel()
        try:
          await self._process_task
        except asyncio.CancelledError:
          pass

  def get_stats(self) -> Dict[str, Any]:
    """Get detailed performance statistics"""
    return {
      **self.metrics,
      "queue_size": self._queue.qsize(),
      "avg_batch_time": self.metrics["batch_processing_times"].mean(),
      "avg_queue_pressure": self.metrics["queue_pressure"].mean(),
      "avg_batch_size": self.metrics["batch_sizes"].mean(),
      "mode": self.mode.value,
      "min_batch_time": self.metrics["batch_processing_times"].min(),
      "max_batch_time": self.metrics["batch_processing_times"].max(),
      "current_batch_size": self._batcher.current_size,
    }

