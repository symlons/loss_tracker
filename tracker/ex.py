import unittest
import time
import aiohttp
import asyncio
import json
import gzip
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
import random
import threading
import queue
from aiohttp import web
from metric_logger import LoggerManager, MetricLogger, RollingStats, MetricBuffer


class TestMetricBuffer(unittest.TestCase):
  """Test cases for the MetricBuffer class"""

  def setUp(self):
    self.buffer = MetricBuffer(initial_size=10)

  def test_buffer_resize(self):
    """Test buffer resizing functionality"""
    initial_size = len(self.buffer.metrics)
    self.buffer.ensure_capacity(20)
    self.assertGreaterEqual(len(self.buffer.metrics), 20)

    # Test exponential growth
    self.buffer.ensure_capacity(50)
    self.assertGreaterEqual(len(self.buffer.metrics), 50)

  def test_buffer_clear(self):
    """Test buffer clearing with active indices tracking"""
    self.buffer.metrics[0] = {"test": 1}
    self.buffer._active_indices.append(0)
    self.buffer.grouped["test"].append(1)

    self.buffer.clear()
    self.assertIsNone(self.buffer.metrics[0])
    self.assertEqual(len(self.buffer.grouped), 0)
    self.assertEqual(len(self.buffer._active_indices), 0)

  def test_initial_buffer_state(self):
    """Test initial buffer state"""
    self.assertEqual(len(self.buffer.metrics), 10)
    self.assertEqual(len(self.buffer._active_indices), 0)
    self.assertEqual(len(self.buffer.grouped), 0)


class TestRollingStats(unittest.TestCase):
  """Test cases for the RollingStats class"""

  def setUp(self):
    self.stats = RollingStats(window_size=5)

  def test_rolling_window(self):
    """Test rolling window statistics"""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    for v in values:
      self.stats.add(v)
    self.assertEqual(self.stats.mean(), 3.0)

    # Add one more value (should roll over)
    self.stats.add(6.0)
    self.assertEqual(self.stats.mean(), 4.0)

  def test_empty_stats(self):
    """Test statistics with no values"""
    self.assertEqual(self.stats.mean(), 0.0)


class MockHTTPServer:
  """Mock HTTP server for testing metric sending"""

  def __init__(self, host="127.0.0.1", port=8080):
    self.host = host
    self.port = port
    self.app = web.Application()
    self.app.router.add_post("/metrics", self.handle_metrics)
    self.received_metrics = []
    self.runner = None
    self.site = None

  async def handle_metrics(self, request):
    """Handle incoming metrics"""
    try:
      content_encoding = request.headers.get("Content-Encoding")
      if content_encoding == "gzip":
        data = await request.read()
        data = gzip.decompress(data)
        data = data.decode("utf-8")
      else:
        data = await request.text()

      self.received_metrics.append(json.loads(data))
      return web.Response(text="OK")
    except Exception as e:
      return web.Response(text=str(e), status=500)

  async def start(self):
    """Start the mock server"""
    self.runner = web.AppRunner(self.app)
    await self.runner.setup()
    self.site = web.TCPSite(self.runner, self.host, self.port)
    await self.site.start()

  async def stop(self):
    """Stop the mock server"""
    if self.site:
      await self.site.stop()
    if self.runner:
      await self.runner.cleanup()


class TestMetricLogger(unittest.TestCase):
  """Test cases for the MetricLogger class"""

  @classmethod
  def setUpClass(cls):
    # Create new event loop for tests
    cls.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(cls.loop)
    # Start mock server for HTTP tests
    cls.mock_server = MockHTTPServer()
    cls.loop.run_until_complete(cls.mock_server.start())

  @classmethod
  def tearDownClass(cls):
    # Stop mock server and cleanup
    cls.loop.run_until_complete(cls.mock_server.stop())
    cls.loop.close()

  def setUp(self):
    self.logger = MetricLogger("test", max_queue_size=100, initial_batch_size=10)
    self.http_logger = MetricLogger(
      "test_http", endpoint="http://127.0.0.1:5005/batch", max_queue_size=100, initial_batch_size=10, enable_compression=True
    )
    self.logger.start()
    self.http_logger.start()

  def tearDown(self):
    if hasattr(self, "logger") and self.logger:
      self.logger.stop(timeout=1.0)
    if hasattr(self, "http_logger") and self.http_logger:
      self.http_logger.stop(timeout=1.0)

  def test_basic_logging(self):
    """Test basic logging functionality"""
    for i in range(5):
      success = self.logger.log({"value": i})
      self.assertTrue(success)

    time.sleep(0.1)
    stats = self.logger.get_stats()
    self.assertGreaterEqual(stats["processed_count"], 5)
    self.assertEqual(stats["dropped_count"], 0)

  def test_http_logging(self):
    """Test HTTP logging functionality"""
    test_metrics = [{"value": i} for i in range(5)]
    for metric in test_metrics:
      success = self.http_logger.log(metric)
      self.assertTrue(success)

    # Give time for async processing
    time.sleep(0.5)

    stats = self.http_logger.get_stats()
    self.assertGreaterEqual(stats["processed_count"], 5)
    self.assertEqual(stats["failed_batches"], 0)

  def test_queue_size_fallback(self):
    """Test queue size fallback mechanism"""
    logger = MetricLogger("test_fallback")
    logger.start()

    # Log some metrics
    for i in range(10):
      logger.log({"value": i})

    # Check if we can get queue size
    size = logger._get_queue_size()
    self.assertIsInstance(size, int)
    self.assertGreaterEqual(size, 0)

    logger.stop()

  def test_high_volume_logging(self):
    """Test logging under high volume"""
    total_metrics = 1000
    successful = 0

    for i in range(total_metrics):
      if self.logger.log({"value": i}):
        successful += 1

    time.sleep(0.5)
    stats = self.logger.get_stats()
    self.assertGreaterEqual(stats["processed_count"], successful - stats["dropped_count"])

  def test_concurrent_logging(self):
    """Test concurrent logging from multiple threads"""
    metrics_per_thread = 25
    num_threads = 4
    event = threading.Event()
    success_count = 0

    def log_metrics():
      nonlocal success_count
      event.wait()
      for i in range(metrics_per_thread):
        if self.logger.log({"value": i}):
          success_count += 1

    threads = []
    for _ in range(num_threads):
      t = threading.Thread(target=log_metrics)
      t.start()
      threads.append(t)

    event.set()
    for t in threads:
      t.join()

    # Give more time for processing
    time.sleep(1.0)

    stats = self.logger.get_stats()
    self.assertGreaterEqual(
      stats["processed_count"] + stats["dropped_count"], success_count, f"Expected at least {success_count} metrics to be processed or dropped"
    )

  def test_graceful_shutdown(self):
    """Test graceful shutdown with pending metrics"""
    num_metrics = 50
    for i in range(num_metrics):
      self.logger.log({"value": i})

    self.logger.stop(timeout=1.0)
    stats = self.logger.get_stats()
    self.assertGreaterEqual(stats["processed_count"] + stats["dropped_count"], num_metrics)

  def test_buffer_reuse(self):
    """Test buffer reuse efficiency"""
    for batch in range(5):
      for i in range(10):
        self.logger.log({"batch": batch, "value": i})
      time.sleep(0.1)  # Give time between batches

    stats = self.logger.get_stats()
    self.assertGreaterEqual(stats["processed_count"], 50)
    self.assertEqual(stats["dropped_count"], 0)


class TestLoggerManager(unittest.TestCase):
  """Test cases for the LoggerManager class"""

  def setUp(self):
    self.manager = LoggerManager(default_batch_size=20)

  def tearDown(self):
    if hasattr(self, "manager"):
      self.manager.stop(timeout=1.0)

  def test_multiple_loggers(self):
    """Test managing multiple loggers"""
    self.manager.add_logger("metrics1", "Test Metrics 1")
    self.manager.add_logger("metrics2", "Test Metrics 2", endpoint="http://127.0.0.1:5005/batch", enable_compression=True)

    num_metrics = 20
    for i in range(num_metrics):
      self.manager.log("metrics1", {"value": i})
      self.manager.log("metrics2", {"value": i * 2})

    time.sleep(0.3)
    stats = self.manager.get_stats()
    for logger_name in ["metrics1", "metrics2"]:
      logger_stats = stats[logger_name]
      self.assertGreaterEqual(logger_stats["processed_count"] + logger_stats["dropped_count"], num_metrics)

  def test_nonexistent_logger(self):
    """Test logging to nonexistent logger"""
    result = self.manager.log("nonexistent", {"value": 1})
    self.assertFalse(result)

  def test_duplicate_logger(self):
    """Test adding duplicate logger"""
    self.manager.add_logger("metrics1", "Test Metrics 1")
    self.manager.add_logger("metrics1", "Test Metrics 1")  # Should print warning
    self.assertEqual(len(self.manager.loggers), 1)


if __name__ == "__main__":
  unittest.main()
