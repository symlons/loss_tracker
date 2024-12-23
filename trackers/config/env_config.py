import os
from dotenv import load_dotenv
from typing import Dict, Optional
from functools import lru_cache

load_dotenv()


class EnvConfig:
  """Environment-based configuration for API endpoints."""

  def __init__(self):
    self.API_HOST = os.getenv("API_HOST", "dev")
    self.default_hosts: Dict[str, str] = {
      "dev": "http://127.0.0.1:5005/batch",
      "minikube": "http://127.0.0.1/api/loss_charting",
      "prod": "http://127.0.0.1:5005/batch",
    }

  @property
  def api_host(self) -> str:
    """Get the API host based on environment configuration."""
    print(self.API_HOST)
    if self.API_HOST not in self.default_hosts:
      raise ValueError(
        f"Unknown HOST value: {self.API_HOST}. " f"Allowed values are: {', '.join(self.default_hosts.keys())}"
      )
    return self.default_hosts[self.API_HOST]

  @classmethod
  @lru_cache(maxsize=1)
  def get_instance(cls) -> "EnvConfig":
    """Get or create singleton instance of EnvConfig."""
    return cls()
