1. Metrics Buffer Memory Optimization
Problem: A deque with a large maxlen (e.g., 500,000) preallocates memory for its full capacity, leading to high memory usage (~50MB or more) even if the buffer is not fully utilized. This becomes a problem for systems with limited RAM or applications running multiple instances of MetricLogger.
Solution: Monitor the buffer size and proactively flush smaller chunks of metrics when the buffer exceeds a critical size (e.g., 80% of its maximum capacity). This reduces peak memory usage and ensures memory is freed dynamically.

2. Concurrency
Problem: The use of asyncio.Lock in _process_metrics creates a single consumer model, which can limit throughput and performance under high logging rates due to lock contention. Producers (logging tasks) must wait for the lock to release, slowing down the overall system.
Solution: Replace the locking mechanism with an asyncio.Queue, allowing producers and consumers to operate independently. This decoupling improves concurrency, eliminates lock contention, and enables smoother scaling under high loads. The queue also provides built-in backpressure by pausing producers if the queue becomes full.



curl -X POST http://mlstatstracker.org/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "name": "batch1",
    "xCoordinates": [1.1, 2.2, 3.3],
    "yCoordinates": [4.4, 5.5, 6.6]
  }'

update kube rollout for server in ci/cd

curl -X POST http://mlstatstracker.org/api/query \
  -H "Content-Type: application/json" \
  -d '{"query_name": "batch1"}'


curl -X POST http://localhost:5005/batch \
  -H "Content-Type: application/json" \
  -d '{
    "name": "batch1",
    "xCoordinates": [1.1, 2.2, 3.3],
    "yCoordinates": [4.4, 5.5, 6.6]
  }'

curl -X POST http://localhost:5005/query \
  -H "Content-Type: application/json" \
  -d '{"query_name": "batch1"}'

