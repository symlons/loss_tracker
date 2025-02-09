import asyncio
import aiohttp
import time
import json
import gzip
import random
from typing import Dict, Any, Optional, Deque, List
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class MetricConfig:
  name: str
  endpoint: Optional[str] = None
  retry_attempts: int = 3
  retry_delay: float = 0.5
  enable_compression: bool = False


class MetricLogger:
  def __init__(self, config: MetricConfig):
    self.config = config
    self._buffers: Dict[str, Deque[Dict[str, Any]]] = defaultdict(deque)
    self._stop_event = asyncio.Event()
    self._buffer_lock = asyncio.Lock()

    self.metrics: Dict[str, int] = {
      "total_logged": 0,
      "total_sent": 0,
      "total_pending": 0,
      "send_failures": 0,
    }
    self._process_task = asyncio.create_task(self._process_metrics())

  async def log(self, step: float, value: float, metric_type: str) -> bool:
    if self._stop_event.is_set():
      return False

    try:
      metric_name = f"{self.config.name}_{metric_type}"
      metric = {
        "name": metric_name,
        "step": float(step),
        "value": float(value),
        "timestamp": time.monotonic(),
      }
      async with self._buffer_lock:
        self._buffers[metric_name].append(metric)
        self.metrics["total_logged"] += 1
        self.metrics["total_pending"] += 1
      return True
    except Exception as e:
      print(f"Logging error: {e}")
      return False

  async def _send_pending_metrics(self, metric_name: str) -> None:
    async with aiohttp.ClientSession() as session:
      async with self._buffer_lock:
        batch = list(self._buffers[metric_name])
        if not batch:
          return

        grouped = {
          "xCoordinates": [m["step"] for m in batch],
          "yCoordinates": [m["value"] for m in batch],
        }

        try:
          await self._send_batch(session, metric_name, grouped)
          count = len(batch)
          self.metrics["total_sent"] += count
          self.metrics["total_pending"] -= count
          self._buffers[metric_name].clear()
        except Exception as send_error:
          print(f"Send failed for {metric_name}: {send_error}")
          self.metrics["send_failures"] += 1

  async def _process_metrics(self) -> None:
    while not self._stop_event.is_set() or any(self._buffers):
      for metric_name in list(self._buffers):
        await self._send_pending_metrics(metric_name)
      await asyncio.sleep(0.1)

  async def _send_batch(self, session: aiohttp.ClientSession, name: str, data: Dict[str, List[float]]) -> None:
    if not self.config.endpoint:
      return

    payload = {
      "name": name,
      "xCoordinates": [float(x) for x in data["xCoordinates"]],
      "yCoordinates": [float(y) for y in data["yCoordinates"]],
    }

    headers = {"Content-Type": "application/json"}
    if self.config.enable_compression:
      payload = gzip.compress(json.dumps(payload).encode("utf-8"))
      headers["Content-Encoding"] = "gzip"

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

  async def stop(self, timeout: float = 1.0) -> None:
    self._stop_event.set()
    try:
      await asyncio.wait_for(self._process_task, timeout=timeout)
    except asyncio.TimeoutError:
      print(f"Processing did not complete within {timeout} seconds.")
      self._process_task.cancel()

    async with aiohttp.ClientSession() as session:
      async with self._buffer_lock:
        buffers_snapshot = {name: list(buf) for name, buf in self._buffers.items() if buf}
      for name, batch in buffers_snapshot.items():
        if batch:
          grouped = {
            "xCoordinates": [m["step"] for m in batch],
            "yCoordinates": [m["value"] for m in batch],
          }
          try:
            await self._send_batch(session, name, grouped)
          except Exception as e:
            print(f"Final send attempt failed for {name}: {e}")

    print("Final Metrics Logging Stats:")
    for key, value in self.get_stats().items():
      print(f"{key}: {value}")

  def get_stats(self) -> Dict[str, Any]:
    total_pending = sum(len(buf) for buf in self._buffers.values())
    return {**self.metrics, "buffer_size": total_pending}


async def simulate_training() -> None:
  config = MetricConfig(
    name="model_training",
    endpoint="http://localhost:5005/batch",
  )
  logger = MetricLogger(config)

  try:
    num_epochs = 10
    steps_per_epoch = 1000
    for epoch in range(num_epochs):
      for step in range(steps_per_epoch):
        global_step = epoch * steps_per_epoch + step
        loss = random.random()
        await logger.log(global_step, loss, "loss")

        if step % 200 == 0:
          await asyncio.sleep(0.011)  # Simulate some processing time
    print("DONE")
  finally:
    await logger.stop()
    print("done")


if __name__ == "__main__":
  asyncio.run(simulate_training())
