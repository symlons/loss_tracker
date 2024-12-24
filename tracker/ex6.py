import asyncio
import random
import math
from metric_logger import MetricLogger, MetricConfig


async def simulate_training():
  """Simulate a training loop with realistic metric values"""
  # Configure the logger
  config = MetricConfig(
    name="model_training",
    endpoint="http://localhost:5005/batch",
    batch_size=500,
    enable_compression=False,  # Disable compression for testing
    retry_attempts=3,
  )

  # Initialize logger
  logger = MetricLogger(config)

  try:
    # Training parameters
    num_epochs = 10
    steps_per_epoch = 1000
    initial_loss = 2.5
    initial_accuracy = 0.3

    print("Starting training simulation...")

    # Main training loop
    for epoch in range(num_epochs):
      print(f"\nEpoch {epoch + 1}/{num_epochs}")

      for step in range(steps_per_epoch):
        # Calculate global step for continuous metrics
        global_step = epoch * steps_per_epoch + step

        # Simulate training metrics
        loss = initial_loss * math.exp(-0.001 * global_step) + random.uniform(-0.1, 0.1)
        accuracy = initial_accuracy + (1 - initial_accuracy) * (1 - math.exp(-0.001 * global_step))
        accuracy = max(0.0, min(1.0, accuracy + random.uniform(-0.05, 0.05)))

        # Log training metrics
        await logger.log(global_step, loss, metric_type="loss")
        await logger.log(global_step, accuracy, metric_type="accuracy")

        # Validation metrics every 50 steps
        if step % 50 == 0:
          val_loss = loss * 1.1 + random.uniform(-0.05, 0.05)
          val_accuracy = accuracy * 0.95 + random.uniform(-0.02, 0.02)
          await logger.log(global_step, val_loss, metric_type="val_loss")
          await logger.log(global_step, val_accuracy, metric_type="val_accuracy")

        # Print progress and logger stats every 25 steps
        if step % 25 == 0:
          print(f"\nStep {step + 1}/{steps_per_epoch}")
          print(f"Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
          stats = logger.get_stats()
          print(f"Queue Size: {stats['queue_size']}")
          print(f"Processed: {stats['processed_count']}")
          print(f"Dropped: {stats['dropped_count']}")
          print(f"Failed: {stats['failed_batches']}")

        # Simulate some computation time (optional, for realism)
        # await asyncio.sleep(0.01)

    print("\nTraining completed. Running final evaluation...")

    # Log final evaluation metrics
    final_loss = initial_loss * math.exp(-0.001 * num_epochs * steps_per_epoch)
    final_accuracy = 0.92 + random.uniform(-0.02, 0.02)

    await logger.log(num_epochs * steps_per_epoch, final_loss, metric_type="final_loss")
    await logger.log(num_epochs * steps_per_epoch, final_accuracy, metric_type="final_accuracy")

    print(f"\nFinal Metrics:")
    print(f"Loss: {final_loss:.4f}")
    print(f"Accuracy: {final_accuracy:.4f}")

  finally:
    print("\nShutting down logger...")
    await logger.stop()
    print("Logger stopped successfully.")


if __name__ == "__main__":
  # Run the simulation
  asyncio.run(simulate_training())

