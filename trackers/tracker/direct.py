import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

data = {
  "name": "test_tracker",
  "xCoordinates": [1, 2, 3],
  "yCoordinates": [0.1, 0.2, 0.3],
  "metadata": {"test": "debug"},
}

try:
  # First check if server is running
  response = requests.get("http://localhost:5005/test")
  print("Server test response:", response.status_code)

  # Then try batch endpoint
  response = requests.post(
    "http://localhost:5005/batch", json=data, headers={"Content-Type": "application/json"}, timeout=5
  )
  print("Batch response:", response.status_code, response.text)
except requests.exceptions.ConnectionError as e:
  print("Connection failed - is server running?", e)
except Exception as e:
  print("Other error:", e)

