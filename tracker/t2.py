from tracker.tracks import log
import numpy as np
import threading
import queue
import time


def run_tracker(queue, stop_event):
  tracker = log(name="b")
  while not stop_event.is_set():
    try:
      metric = queue.get(timeout=0.5)
      tracker.push(metric)
    except:
      pass


def main():
  metrics_queue = queue.Queue()
  stop_event = threading.Event()

  tracker_thread = threading.Thread(target=run_tracker, args=(metrics_queue, stop_event))
  tracker_thread.start()

  for epoch in range(2):
    for i in range(100):
      metric = np.sin(i / 10) + np.random.normal(0, 0.1)

      metrics_queue.put(metric)

      print(f"Epoch {epoch}, Step {i}")
  print("done")

  stop_event.set()
  tracker_thread.join(timeout=2.0)


if __name__ == "__main__":
  main()
