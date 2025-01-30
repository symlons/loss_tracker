import asyncio
import random
import numpy as np
from metric_logger import MetricLogger, MetricConfig

from dotenv import load_dotenv
import os


class Config:
  def __init__(self):
    load_dotenv()
    self.default_hosts = {
      "dev": "http://localhost:5005/batch",
      "minikube": "http://127.0.0.1/api/batch",
      "prod": "http://mlstatstracker.org:3005/api/batch",
    }
    self.api_host = self.default_hosts.get(os.getenv("API_HOST", "minikube"), None)
    print(self.api_host)
    if self.api_host is None:
      raise ValueError(f"Invalid API_HOST. Choose from {', '.join(self.default_hosts.keys())}.")


async def simulate_ml_training():
  config = MetricConfig(
    name="advanced_ml_experiment",
    endpoint=Config().api_host,
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
      loss = np.random.exponential(scale=0.1)
      accuracy = min(1.0, max(0.0, random.gauss(0.9, 0.05)))
      learning_rate = 0.001 * (0.95**epoch)

      await logger.log(epoch, loss, "loss")
      await logger.log(epoch, accuracy, "accuracy")
      await logger.log(epoch, learning_rate, "learning_rate")

      if epoch % 1000 == 0:
        print(f"Processing epoch {epoch}")
        await asyncio.sleep(0.02)

  except Exception as e:
    print(f"Training interrupted: {e}")
  finally:
    print("training already finished ------------------------------")
    await logger.stop()  # ensures all metrics are sent

    print("\nTraining Metrics Summary:")
    stats = logger.get_stats()
    for key, value in stats.items():
      print(f"{key}: {value}")


async def main():
  await simulate_ml_training()


if __name__ == "__main__":
  asyncio.run(main())
