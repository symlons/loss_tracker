import time
from tracker import xy
import random


def train_step(epoch):
  loss = max(0.1, 1.0 - (epoch * 0.01)) + random.gauss(0, 0.05)
  accuracy = min(1.0, 0.5 + (epoch * 0.005)) + random.gauss(0, 0.02)
  return loss, accuracy


def training_loop():
  loss_tracker = xy(name="training_loss")
  accuracy_tracker = xy(name="training_accuracy")
  trackers = [loss_tracker, accuracy_tracker]

  num_epochs = 1000
  print("Starting training loop...")
  start_time = time.time()

  for epoch in range(num_epochs):
    loss, accuracy = train_step(epoch)
    loss_tracker.push(epoch, loss)
    accuracy_tracker.push(epoch, accuracy)
    if epoch % 10 == 0:
      print(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")

  print("\nFlushing and processing remaining batches...")
  while any(tracker.manager.batch_queue.qsize() > 0 for tracker in trackers):
    queue_sizes = {tracker.name: tracker.manager.batch_queue.qsize() for tracker in trackers}
    print(f"Waiting for batches... {queue_sizes}")
    time.sleep(1)

  for tracker in trackers:
    tracker.close()

  end_time = time.time()
  print(f"\nTraining completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
  training_loop()
