import asyncio
import random
from ..trackers import xy
from ..config.tracker_config import TrackerConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


async def async_train_step(epoch: int) -> tuple[float, float]:
  """Simulate an async training step."""
  await asyncio.sleep(0.01)  # Simulate some async work
  base_loss = max(0.1, 1.0 - (epoch * 0.01))
  noise = random.gauss(0, 0.05)
  loss = base_loss + noise
  accuracy = min(1.0, 0.5 + (epoch * 0.005))
  accuracy_noise = random.gauss(0, 0.02)
  accuracy += accuracy_noise
  return loss, accuracy


async def async_training_loop(num_epochs: int = 1000):
  """Example async training loop using trackers."""
  config = TrackerConfig(max_workers=4)

  async with (
    xy(name="async_training_loss", config=config) as loss_tracker,
    xy(name="async_training_accuracy", config=config) as accuracy_tracker,
  ):
    logger.info("Starting async training loop...")

    for epoch in range(num_epochs):
      loss, accuracy = await async_train_step(epoch)
      await loss_tracker.push(epoch, loss)
      await accuracy_tracker.push(epoch, accuracy)
      if epoch % 10 == 0:
        logger.info(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")


if __name__ == "__main__":
  asyncio.run(async_training_loop())
