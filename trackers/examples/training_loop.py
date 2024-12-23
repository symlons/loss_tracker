import logging
import random
from tqdm import tqdm
import time
from trackers.trackers.log_tracker import log  # Change to use log instead of xy
from trackers.config.tracker_config import TrackerConfig
from trackers.utils.logging import get_logger

logger = get_logger(__name__)


def train_step(epoch: int) -> tuple[float, float]:
  """Simulate a training step with synthetic loss and accuracy."""
  base_loss = max(0.1, 1.0 - (epoch * 0.01))
  noise = random.gauss(0, 0.05)
  loss = base_loss + noise
  accuracy = min(1.0, 0.5 + (epoch * 0.005))
  accuracy_noise = random.gauss(0, 0.02)
  accuracy += accuracy_noise
  return loss, accuracy


def training_loop(num_epochs: int = 200):
  """Example training loop using trackers."""
  import os

  os.environ["API_HOST"] = "dev"

  config = TrackerConfig(
    use_mock_api=False,
    batch_size=5,
  )

  logger.info("Starting training loop with config: %s", config)

  with (
    log(name="training_loss", config=config, block_size=5) as loss_tracker,
    log(name="training_accuracy", config=config, block_size=5) as accuracy_tracker,
  ):
    logger.info("Starting training loop...")
    start_time = time.time()

    for epoch in tqdm(range(num_epochs), desc="Training Progress"):
      loss, accuracy = train_step(epoch)
      logger.debug(f"Epoch {epoch}: pushing loss={loss:.4f}, accuracy={accuracy:.4f}")
      loss_tracker.push(loss)  # Changed: only pass y value
      accuracy_tracker.push(accuracy)  # Changed: only pass y value
      if epoch % 5 == 0:
        logger.info(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")

    end_time = time.time()
    logger.info(f"Training completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  training_loop()
