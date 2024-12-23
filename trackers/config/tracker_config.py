from dataclasses import dataclass, field
from typing import Dict, Optional, Callable
from .env_config import EnvConfig


@dataclass(frozen=True)
class TrackerConfig:
  """Configuration for tracker behavior and API settings."""

  batch_size: int = field(default=100)
  max_retries: int = field(default=3)
  timeout: float = field(default=10.0)
  max_workers: int = field(default=4)
  use_mock_api: bool = field(default=False)
  daemon: bool = field(default=True)
  test_mode: bool = field(default=False)
  test_callbacks: Dict[str, Callable] = field(default_factory=dict)
  _env_config: EnvConfig = field(default_factory=EnvConfig.get_instance)

  def __post_init__(self):
    if self.batch_size <= 0:
      raise ValueError("batch_size must be positive")
    if self.max_retries < 0:
      raise ValueError("max_retries cannot be negative")
    if self.timeout <= 0:
      raise ValueError("timeout must be positive")
    if self.max_workers <= 0:
      raise ValueError("max_workers must be positive")

  @property
  def api_host(self) -> str:
    """Get the API host from environment configuration."""
    return self._env_config.api_host
