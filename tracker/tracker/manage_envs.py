import os
from dotenv import load_dotenv

load_dotenv()


class Config:
  def __init__(self):
    self.API_HOST = os.getenv("API_HOST", "prod")
    self.default_hosts = {
      "dev": "http://127.0.0.1:5005/loss_charting",
      "minikube": "http://127.0.0.1/api/loss_charting",
      "prod": "http://mlstatstracker.org/api/loss_charting",
    }

  @property
  def api_host(self):
    if self.API_HOST not in self.default_hosts:
      raise ValueError(
        f"Unknown HOST value: {self.API_HOST}. " f"Allowed values are: {', '.join(self.default_hosts.keys())}"
      )
    return self.default_hosts[self.API_HOST]


if __name__ == "__main__":
  config = Config()
  print(f"Using API Host: {config.api_host}")
