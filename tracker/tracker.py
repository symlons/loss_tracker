import requests as rq

host = "http://localhost:5005/api/loss_charting"
session = rq.Session()

class xy:
    x_list = []
    y_list = []
    def __init__(self, x, y, name='first', block_size=1000):
        self.block_size = block_size
        self.post(x, y, name)

    def post(self, x, y, name, host="http://localhost:5005/api/loss_charting"):

        if type(x) == list:
            self.x_list.extend(x)
            self.y_list.extend(y)
        else:
            self.x_list.extend([x])
            self.y_list.extend([y])
        if len(self.x_list) % self.block_size == 0:
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': name})
            xy.x_list = []
            xy.y_list = []

class log:
    y_list = []
    x_list = [0]
    def __init__(self, y, name='first', block_size=1000):
        self.block_size = block_size
        self.post(y, name)

    def post(self, y, name, host="http://localhost:5005/api/loss_charting"):
        self.x_list.append(self.x_list[-1] + self.block_size)
        if type(y) == list:
            self.y_list.extend(y)
        else:
            self.y_list.extend([y])
        if len(self.y_list) % self.block_size == 0:
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': name})
            log.x_list = [self.x_list[-1]]
            log.y_list = []

    def zero_track(self):
        log.x_list = [0]
        log.y_list = []

