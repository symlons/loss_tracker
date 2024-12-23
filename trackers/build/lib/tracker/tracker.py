import requests as rq
from tracker.manage_envs import Config

session = rq.Session()


class xy:
  def __init__(self, *, name="first", block_size=100):
    self.block_size = block_size
    self.name = name
    self.x_list = []
    self.y_list = []
    self.host = Config().api_host

  def push(self, x, y):
    if hasattr(x, "__iter__"):
      self.x_list.extend(x)
      self.y_list.extend(y)
    else:
      self.x_list.extend([x])
      self.y_list.extend([y])
    if len(self.x_list) % self.block_size == 0:
      session.post(
        self.host,
        json={
          "yCoordinates": self.y_list,
          "xCoordinates": self.x_list,
          "name": self.name,
        },
      )
      self.x_list = []
      self.y_list = []

  def zero_track(self):
    self.x_list = [0]
    self.y_list = []


class log:
  def __init__(self, *, name="first", block_size=2):
    self.name = name
    self.y_list = []
    self.x_list = [0]
    self.x_count = 0
    self.block_size = block_size
    self.host = Config().api_host

  def push(self, y):
    if hasattr(y, "__iter__"):
      self.x_list.extend([i for i in range(self.x_list[-1] + 1, len(y))])
      self.y_list.extend(y)
    else:
      self.x_list.extend([self.x_count])
      self.y_list.extend([y])
      self.x_count += 1
    if len(self.y_list) % self.block_size == 0:
      session.post(
        self.host,
        json={
          "yCoordinates": self.y_list,
          "xCoordinates": self.x_list,
          "name": self.name,
        },
      )

      self.x_list = []
      self.y_list = []

  def zero_track(self):
    self.x_list = [0]
    self.y_list = []
