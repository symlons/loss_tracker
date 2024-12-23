from dataclasses import dataclass, field
from typing import List
from time import perf_counter


@dataclass
class MetricsCollector:
  """Collector for tracking metrics about batch processing."""

  sent_batches: int = 0
  failed_batches: int = 0
  queued_batches: int = 0
  total_processing_time: float = 0.0
  batch_processing_times: List[float] = field(default_factory=list)

  def add_processing_time(self, duration: float):
    """Add a processing time measurement."""
    self.total_processing_time += duration
    self.batch_processing_times.append(duration)

  @property
  def average_processing_time(self) -> float:
    """Calculate average processing time."""
    return self.total_processing_time / len(self.batch_processing_times) if self.batch_processing_times else 0.0

