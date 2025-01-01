import asyncio
import random
import numpy as np
from metric_logger import MetricLogger, MetricConfig


async def simulate_ml_training():
  """Simulate a complex machine learning training scenario"""
  config = MetricConfig(
    name="advanced_ml_experiment",
    endpoint="http://localhost:5005/batch",
    max_buffer_size=100000,
    batch_size=100,
    retry_attempts=5,
    retry_delay=0.5,
    enable_compression=True,
  )
  logger = MetricLogger(config)

  try:
    num_epochs = 5000
    for epoch in range(num_epochs):
      # Simulate training metrics with varying characteristics
      loss = np.random.exponential(scale=0.1)
      accuracy = min(1.0, max(0.0, random.gauss(0.9, 0.05)))
      learning_rate = 0.001 * (0.95**epoch)

      # Log multiple metrics per epoch
      await logger.log(epoch, loss, "loss")
      await logger.log(epoch, accuracy, "accuracy")
      await logger.log(epoch, learning_rate, "learning_rate")

      if epoch % 1000 == 0:
        print(f"Processing epoch {epoch}")
        await asyncio.sleep(0.02)

  except Exception as e:
    print(f"Training interrupted: {e}")
  finally:
    # Ensure all metrics are sent
    print("training already finished ------------------------------")
    await logger.stop()

    print("\nTraining Metrics Summary:")
    stats = logger.get_stats()
    for key, value in stats.items():
      print(f"{key}: {value}")


async def main():
  await simulate_ml_training()


if __name__ == "__main__":
  asyncio.run(main())
