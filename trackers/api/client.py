import requests
import logging
import aiohttp
import asyncio
from typing import Any, List, Union, Dict
from ..config.tracker_config import TrackerConfig
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


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
      logger.info(f"Mock API mode: Simulating successful batch send for {batch_data['name']}")
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
