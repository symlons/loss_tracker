import math
import random
import time
from tracker import xy, log, XYTracker, LogTracker, TrackerConfig, BatchPriority


def test_single_batch():
  tracker = xy(name="learning_curve")
  for i in range(10000):
    tracker.push(i, random.gauss(0.1, 0.5))
  # Flush only at the end
  tracker.close()


if __name__ == "__main__":
  print("Starting tracker test...")
  start_time = time.time()
  test_single_batch()
  print(f"Test completed in {time.time() - start_time:.2f} seconds")

