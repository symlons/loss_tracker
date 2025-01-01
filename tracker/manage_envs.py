import os
from dotenv import load_dotenv


class Config:
  def __init__(self):
    # Load the .env file when an instance of Config is created
    load_dotenv()

    self.API_HOST = os.getenv("API_HOST", "minikube")
    self.default_hosts = {
      "dev": "http://127.0.0.1:5005/batch",
      "minikube": "http://127.0.0.1/api/batch",
      "prod": "http://mlstatstracker.org/api/batch",
    }

  @property
  def api_host(self):
    if self.API_HOST not in self.default_hosts:
      raise ValueError(f"Unknown HOST value: {self.API_HOST}. Allowed values are: {', '.join(self.default_hosts.keys())}")
    return self.default_hosts[self.API_HOST]
