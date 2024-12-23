import pytest
from ..trackers import xy, log
from ..config import TrackerConfig
from ..models import BatchPriority


def test_xy_tracker_initialization():
  tracker = xy(name="test", block_size=50)
  assert tracker.name == "test"
  assert tracker.config.batch_size == 50
  assert tracker.priority == BatchPriority.NORMAL


def test_xy_tracker_push_single():
  tracker = xy(name="test", block_size=2)
  tracker.push(1, 2)
  assert tracker.x_data == [1]
  assert tracker.y_data == [2]


def test_xy_tracker_push_multiple():
  tracker = xy(name="test", block_size=5)
  tracker.push([1, 2], [3, 4])
  assert tracker.x_data == [1, 2]
  assert tracker.y_data == [3, 4]
