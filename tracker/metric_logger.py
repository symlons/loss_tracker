import asyncio
import aiohttp
import time
import json
import gzip
import random
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from array import array


@dataclass
class MetricConfig:
  """Configuration for metric collection"""

  name: str
  endpoint: Optional[str] = None
  max_buffer_size: int = 500000  # Large buffer size
  max_memory_buffer_time: float = 300.0  # 5 minutes max buffering
  batch_size: int = 50
  retry_attempts: int = 3
  retry_delay: float = 0.5
  enable_compression: bool = False


class RollingStats:
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

  async def stop(self, timeout: float = 10.0):
    """Graceful shutdown, ensuring all metrics are attempted to be sent"""
    self._stop_event.set()

    try:
      # Wait for processing to complete
      await asyncio.wait_for(self._process_task, timeout=timeout)
    except asyncio.TimeoutError:
      print(f"Processing did not complete within {timeout} seconds.")
      self._process_task.cancel()

    # Print final metrics
    print("Final Metrics Logging Stats:")
    for key, value in self.get_stats().items():
      print(f"{key}: {value}")

  def get_stats(self) -> Dict[str, Any]:
    """Get detailed performance statistics"""
    return {
      **self.metrics,
      "buffer_size": len(self._buffer),
      "avg_batch_time": self.metrics["batch_processing_times"].mean(),
      "avg_batch_size": self.metrics["batch_sizes"].mean(),
      "min_batch_time": self.metrics["batch_processing_times"].min(),
      "max_batch_time": self.metrics["batch_processing_times"].max(),
      "current_batch_size": self._batcher.current_size,
    }


class MetricLogger:
  def __init__(self, config: MetricConfig):
    self.config = config
    self._buffer = deque(maxlen=config.max_buffer_size)
    self._stop_event = asyncio.Event()
    self._buffer_lock = asyncio.Lock()

    # Metrics tracking
    self.metrics = {"total_logged": 0, "total_sent": 0, "total_pending": 0, "send_failures": 0}

    # Start background processing
    self._process_task = asyncio.create_task(self._process_metrics())

  async def log(self, step: float, value: float, metric_type: str, name: Optional[str] = None) -> bool:
    """Log a metric, buffering if immediate send is not possible"""
    if self._stop_event.is_set():
      return False

    try:
      # Use custom name if provided, otherwise use default name
      metric_name = name or f"{self.config.name}_{metric_type}"

      metric = {"name": metric_name, "step": float(step), "value": float(value), "timestamp": time.monotonic()}

      async with self._buffer_lock:
        # Add new metric
        self._buffer.append(metric)
        self.metrics["total_logged"] += 1
        self.metrics["total_pending"] += 1

      return True

    except Exception as e:
      print(f"Logging error: {e}")
      return False

  async def _process_metrics(self):
    """Continuously attempt to send buffered metrics"""
    async with aiohttp.ClientSession() as session:
      while not self._stop_event.is_set() or self._buffer:
        try:
          # Prepare batch
          async with self._buffer_lock:
            if not self._buffer:
              await asyncio.sleep(1)
              continue

            # Group all current metrics by name
            grouped = defaultdict(lambda: {"xCoordinates": [], "yCoordinates": []})
            batch_to_send = list(self._buffer)

            for metric in batch_to_send:
              name = metric["name"]
              grouped[name]["xCoordinates"].append(metric["step"])
              grouped[name]["yCoordinates"].append(metric["value"])

          # Attempt to send batches
          for name, data in grouped.items():
            try:
              await self._send_batch(session, name, data)

              # Remove sent metrics
              async with self._buffer_lock:
                for metric in batch_to_send:
                  if metric in self._buffer:
                    self._buffer.remove(metric)
                    self.metrics["total_sent"] += 1
                    self.metrics["total_pending"] -= 1

            except Exception as send_error:
              print(f"Failed to send batch for {name}: {send_error}")
              self.metrics["send_failures"] += 1

        except Exception as process_error:
          print(f"Processing error: {process_error}")
          await asyncio.sleep(1)

  async def _send_batch(self, session: aiohttp.ClientSession, name: str, data: Dict):
    """Send a batch of metrics with compression and retry"""
    if not self.config.endpoint:
      return

    payload = {"name": name, "xCoordinates": [float(x) for x in data["xCoordinates"]], "yCoordinates": [float(y) for y in data["yCoordinates"]]}

    headers = {"Content-Type": "application/json"}
    if self.config.enable_compression:
      payload_bytes = json.dumps(payload).encode("utf-8")
      payload = gzip.compress(payload_bytes)
      headers["Content-Encoding"] = "gzip"

    # Retry mechanism
    for attempt in range(self.config.retry_attempts):
      try:
        async with session.post(
          self.config.endpoint,
          json=payload if not self.config.enable_compression else None,
          data=payload if self.config.enable_compression else None,
          headers=headers,
          timeout=aiohttp.ClientTimeout(total=2),
        ) as response:
          if response.status < 400:
            return
          else:
            print(f"Failed to send metrics: HTTP {response.status}")
            await asyncio.sleep(self.config.retry_delay * (2**attempt))

      except Exception as e:
        print(f"Error sending batch (attempt {attempt + 1}): {e}")
        await asyncio.sleep(self.config.retry_delay * (2**attempt))

    raise RuntimeError(f"Failed to send metrics for {name} after all retry attempts")

  async def stop(self, timeout: float = 10.0):
    """Graceful shutdown, ensuring all metrics are attempted to be sent"""
    self._stop_event.set()

    try:
      # Wait for processing to complete
      await asyncio.wait_for(self._process_task, timeout=timeout)
    except asyncio.TimeoutError:
      print(f"Processing did not complete within {timeout} seconds.")
      self._process_task.cancel()

    # Final attempt to send any remaining metrics
    if self._buffer:
      try:
        async with aiohttp.ClientSession() as session:
          grouped = defaultdict(lambda: {"xCoordinates": [], "yCoordinates": []})
          for metric in self._buffer:
            name = metric["name"]
            grouped[name]["xCoordinates"].append(metric["step"])
            grouped[name]["yCoordinates"].append(metric["value"])

          for name, data in grouped.items():
            try:
              await self._send_batch(session, name, data)
            except Exception as e:
              print(f"Final send attempt failed for {name}: {e}")

      except Exception as final_error:
        print(f"Error in final metric send: {final_error}")

    # Print final metrics
    print("Final Metrics Logging Stats:")
    for key, value in self.get_stats().items():
      print(f"{key}: {value}")

  def get_stats(self) -> Dict[str, Any]:
    """Get detailed performance statistics"""
    return {**self.metrics, "buffer_size": len(self._buffer)}


async def simulate_training():
  config = MetricConfig(
    name="model_training",
    endpoint="http://localhost:5005/batch",
    batch_size=100,
    max_buffer_size=10000,
    max_memory_buffer_time=60.0,  # 1 minute max buffering
  )
  logger = MetricLogger(config)

  try:
    num_epochs = 10
    steps_per_epoch = 1000
    for epoch in range(num_epochs):
      for step in range(steps_per_epoch):
        global_step = epoch * steps_per_epoch + step
        loss = random.random()
        accuracy = random.random()

        await logger.log(global_step, loss, "loss")
        await logger.log(global_step, accuracy, "accuracy")

        # Simulate occasional processing delays
        if step % 100 == 0:
          await asyncio.sleep(0.01)
  finally:
    await logger.stop()


if __name__ == "__main__":
  asyncio.run(simulate_training())
