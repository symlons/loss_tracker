from dataclasses import dataclass, field
from typing import Dict, Optional, Callable


@dataclass(frozen=True)
class TrackerConfig:
  """Configuration for tracker behavior and API settings."""

  batch_size: int = field(default=100)
  max_retries: int = field(default=3)
  timeout: float = field(default=10.0)
  max_workers: int = field(default=4)
  api_host: str = field(default="http://localhost:5005/batch")
  use_mock_api: bool = field(default=False)
  daemon: bool = field(default=True)
  test_mode: bool = field(default=False)
  test_callbacks: Dict[str, Callable] = field(default_factory=dict)

  def __post_init__(self):
    if self.batch_size <= 0:
      raise ValueError("batch_size must be positive")
    if self.max_retries < 0:
      raise ValueError("max_retries cannot be negative")
    if self.timeout <= 0:
      raise ValueError("timeout must be positive")
    if self.max_workers <= 0:
      raise ValueError("max_workers must be positive")
