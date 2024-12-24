# ex2.py
from metric_logger import MetricLogger
import time


def run_training_logger():
  logger = MetricLogger(
    metric_name="training",
    endpoint="http://localhost:5005/batch",
    # Remove these as they're not in your MetricLogger __init__
    # max_queue_size=1000,
    # min_batch_size=10,
    # max_batch_size=50
  )

  # Remove start() as it's not in your class
  print("Logger started - sending metrics to http://localhost:5005/batch")

  try:
    global_step = 0
    for epoch in range(30):
      print(f"\nStarting epoch {epoch}")

      for batch in range(5):
        # Calculate metrics
        loss = 1.0 - (epoch * 0.1 + batch * 0.01)
        accuracy = 0.7 + (epoch * 0.02 + batch * 0.005)

        # Log loss and accuracy
        success_loss = logger.log(global_step, loss, "loss")
        success_acc = logger.log(global_step, accuracy, "accuracy")

        if success_loss and success_acc:
          print(f"Logged metrics for step {global_step} (epoch {epoch}, batch {batch})")
        else:
          print(f"Warning: Failed to log some metrics at step {global_step}")

        global_step += 1
        time.sleep(0.05)  # Delay between steps

      # Print stats after each epoch
      stats = logger.get_stats()
      print(f"\nEpoch {epoch} Stats:")
      print(f"Processed: {stats['processed_count']}")
      print(f"Dropped: {stats['dropped_count']}")
      print(f"Failed: {stats['failed_batches']}")
      print(f"Queue Size: {stats['queue_size']}")
    print("finished")

  except KeyboardInterrupt:
    print("\nStopping logger gracefully...")
  finally:
    logger.stop()
    print("Logger stopped")


if __name__ == "__main__":
  print("Starting training logger...")
  run_training_logger()
