import requests
import logging
from typing import Any, List, Optional, Union, Dict
from ..config.tracker_config import TrackerConfig
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


# Synchronous API client with retries
class APIClient:
  def __init__(self, config: TrackerConfig):
    self.config = config
    self.session = requests.Session()
    retry_strategy = Retry(
      total=config.max_retries,
      backoff_factor=2,
      status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    self.session.mount("http://", adapter)
    self.session.mount("https://", adapter)
    logger.info(f"Initialized API client with endpoint: {config.api_host}")

  def send_batch(self, batch_data: Dict[str, Any]) -> bool:
    if self.config.use_mock_api:
      logger.info(
        f"Mock API mode: Simulating successful batch send for {batch_data['name']} "
        f"with {len(batch_data['xCoordinates'])} points"
      )
      return True

    try:
      logger.info(f"Sending batch to {self.config.api_host}")
      response = self.session.post(self.config.api_host, json=batch_data, timeout=self.config.timeout)
      if response.status_code == 200:
        logger.info(f"Successfully sent batch to API: {response.status_code}")
      else:
        logger.error(f"API request failed with status code: {response.status_code}")
      return response.status_code == 200
    except requests.exceptions.RequestException as e:
      logger.error(f"API request failed: {e}")
      return False


# Asynchronous API client
class AsyncAPIClient:
  """Asynchronous HTTP client for sending batch data to the API."""

  def __init__(self, config: TrackerConfig):
    self.config = config

  async def send_batch(self, batch_data: Dict[str, Any]) -> bool:
    """Send a batch of data to the API asynchronously."""
    try:
      async with aiohttp.ClientSession() as session:
        async with session.post(self.config.api_host, json=batch_data, timeout=self.config.timeout) as response:
          return response.status == 200
    except Exception as e:
      logger.error(f"Async API request failed: {e}")
      return False


# LogTracker integration
class LogTracker:
  """Tracker for sequential logging data."""

  def __init__(
    self,
    name: str = "first",
    block_size: int = 2,
    config: Optional[TrackerConfig] = None,
    priority: str = "NORMAL",  # Changed for simplicity in this example
  ):
    """Initialize the LogTracker with the provided configurations."""
    # Create a new config with the specified block_size
    config_dict = config.__dict__ if config else {}
    config = TrackerConfig(batch_size=block_size, **{k: v for k, v in config_dict.items() if k != "batch_size"})

    self.config = config
    self.name = name
    self.priority = priority

    # Initialize counters and data lists
    self.x_count = 0
    self.x_data = []  # Store x-values (coordinates or indices)
    self.y_data = []  # Store y-values (values you are tracking)

    # Initialize API Client
    if self.config.use_async_api:
      self.api_client = AsyncAPIClient(self.config)
    else:
      self.api_client = APIClient(self.config)

  def push(self, y: Union[Any, List[Any]]):
    """Push sequential data points to the tracker."""
    if hasattr(y, "__iter__"):  # If it's iterable (list or similar)
      last_x = self.x_data[-1] if self.x_data else 0
      self.x_data.extend(range(last_x + 1, last_x + len(y) + 1))
      self.y_data.extend(y)
    else:  # Single value
      self.x_data.append(self.x_count)
      self.y_data.append(y)
      self.x_count += 1

    # Flush data if the batch size is reached
    if len(self.y_data) >= self.config.batch_size:
      # If using async API, await the flush method to ensure it's completed
      if self.config.use_async_api:
        asyncio.create_task(self.flush())  # Asynchronously execute flush
      else:
        self.flush()

  async def flush(self):
    """Flush the data (send it to the tracker API or process it)."""
    if not self.y_data:
      return  # No data to flush

    # Prepare batch data
    batch_data = {
      "name": f"{self.name}-batch-{len(self.x_data) // self.config.batch_size}",
      "xCoordinates": self.x_data,
      "yCoordinates": self.y_data,
    }

    # Send the batch asynchronously or synchronously depending on the config
    if self.config.use_async_api:
      await self.send_batch_in_order(batch_data)  # Await the batch sending sequentially
    else:
      self.api_client.send_batch(batch_data)

    # Clear data after sending
    self.x_data.clear()
    self.y_data.clear()

  async def send_batch_in_order(self, batch_data: Dict[str, Any]):
    """Ensure batches are sent in order asynchronously."""
    await self.api_client.send_batch(batch_data)


# Convenience alias
log = LogTracker
