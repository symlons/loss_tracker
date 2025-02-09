import asyncio
import random
import numpy as np
import uuid
from metric_logger import MetricLogger, MetricConfig

from dotenv import load_dotenv
import os


class Config:
  def __init__(self):
    load_dotenv()
    self.default_hosts = {
      "dev": "http://localhost:5005/batch",
      "minikube": "http://127.0.0.1/api/batch",
      "prod": "http://mlstatstracker.org/api/batch",
    }
    self.api_host = self.default_hosts.get(os.getenv("API_HOST", "dev"))
    if self.api_host is None:
      raise ValueError(f"Invalid API_HOST. Choose from {', '.join(self.default_hosts.keys())}.")
    print(f"Using API host: {self.api_host}")


async def simulate_ml_training():
  config = MetricConfig(
    name="advanced_ml_experiment",
    endpoint=Config().api_host,
    retry_attempts=5,
    retry_delay=0.5,
    enable_compression=True,
  )

  run_id = str(uuid.uuid4())
  logger = MetricLogger(config, run_id=run_id)

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
    print("Training finished. Sending remaining metrics...")
    await logger.stop()

    print("\nTraining Metrics Summary:")
    stats = logger.get_stats()
    for key, value in stats.items():
      print(f"{key}: {value}")


async def main():
  await simulate_ml_training()


if __name__ == "__main__":
  asyncio.run(main())
