import aiohttp
import logging
from typing import Dict, Any
from ..config.tracker_config import TrackerConfig

logger = logging.getLogger(__name__)


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
