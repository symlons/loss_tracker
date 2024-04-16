import requests as rq

host = "http://localhost:5005/api/loss_charting"
session = rq.Session()

class xy:
    def __init__(self, *, name='first', block_size=1000):
        self.block_size = block_size
        self.name = name
        self.x_list = []
        self.y_list = []
        # self.post(x, y, name)

    def push(self, x, y, host="http://localhost:5005/api/loss_charting"):
        if type(x) == list:
            self.x_list.extend(x)
            self.y_list.extend(y)
        else:
            self.x_list.extend([x])
            self.y_list.extend([y])
        if len(self.x_list) % self.block_size == 0:
            print(type(self.x_list))
            print(type(self.y_list))
            print(type(self.name))
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': self.name})
            self.x_list = []
            self.y_list = []

    def zero_track():
        xy.x_list = [0]
        xy.y_list = []

class log:
    def __init__(self, *, name='first', block_size=100):
        self.name = name
        self.y_list = []
        self.x_list = []
        self.block_size = block_size

    def push(self, y, host="http://localhost:5005/api/loss_charting"):
        if len(self.x_list) == 0:
            self.x_list.append(self.block_size)
        else:
            self.x_list.append(self.x_list[-1] + self.block_size)
        if type(y) == list:
            self.y_list.extend(y)
        else:
            self.y_list.extend([y])
        if len(self.y_list) % self.block_size == 0:
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': self.name})
            self.x_list = [self.x_list[-1]]
            self.y_list = []

    def zero_track(self):
        self.x_list = [0]
        self.y_list = []

