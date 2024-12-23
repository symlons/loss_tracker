from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any
from time import time


class BatchPriority(Enum):
  HIGH = 1
  NORMAL = 2
  LOW = 3


@dataclass(order=True)
class PrioritizedBatch:
  """Batch of data with priority and sequence information."""

  priority: BatchPriority
  sequence_num: int = field(compare=True)  # Add sequence number
  data: Dict[str, Any] = field(compare=False)
  timestamp: float = field(default_factory=time, compare=True)
  retry_count: int = field(default=0, compare=False)
