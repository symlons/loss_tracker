import time
from tracker import xy
import random


def train_step(epoch):
  loss = max(0.1, 1.0 - (epoch * 0.01)) + random.gauss(0, 0.05)
  accuracy = min(1.0, 0.5 + (epoch * 0.005)) + random.gauss(0, 0.02)
  return loss, accuracy


def training_loop():
  loss_tracker, accuracy_tracker = xy(name="training_loss"), xy(name="training_accuracy")
  num_epochs = 10000
  start_time = time.time()

  for epoch in range(num_epochs):
    loss, accuracy = train_step(epoch)
    loss_tracker.push(epoch, loss)
    accuracy_tracker.push(epoch, accuracy)
    if epoch % 10 == 0:
      print(f"Epoch {epoch}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")

  print("Flushing data before shutdown.")
  loss_tracker.flush()
  accuracy_tracker.flush()

  while any(q.qsize() > 0 for q in [loss_tracker.manager.batch_queue, accuracy_tracker.manager.batch_queue]):
    print(
      f"Waiting for batches... (Loss: {loss_tracker.manager.batch_queue.qsize()}, Accuracy: {accuracy_tracker.manager.batch_queue.qsize()})"
    )
    time.sleep(1)

  print("Shutting down background thread.")
  loss_tracker.manager.shutdown(wait=True)
  accuracy_tracker.manager.shutdown(wait=True)

  print(f"Training completed in {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
  training_loop()
