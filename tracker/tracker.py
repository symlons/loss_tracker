import requests as rq

host = "http://localhost:5005/api/loss_charting"
session = rq.Session()

class xy:
    def __init__(self, *, name='first', block_size=100):
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

    def zero_track(self):
        self.x_list = [0]
        self.y_list = []

class log:
    def __init__(self, *, name='first', block_size=2):
        self.name = name
        self.y_list = []
        self.x_list = []
        self.last_x = 0
        self.block_size = block_size

    def push(self, y, host="http://localhost:5005/api/loss_charting"):
        # if len(self.x_list) == 0:
        #     # self.x_list.append(self.block_size)
        #     pass
        # else:
        #     self.x_list.append(self.x_list[-1] + self.block_size)
        if type(y) == list:
            self.x_list.extend(y)
            self.y_list.extend(y)
        else:
            # self.x_list.extend([self.last_x + self.block_size -1]) # is using same value fro size of block_size,
            # to fix might use empty list with empty values having last_x and being length block_size then adding 
            # values of arange block_size
            self.y_list.extend([y])
        if len(self.y_list) % self.block_size == 0:
            print(self.x_list)
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': self.name})
            self.last_x = self.x_list[-1]
            self.x_list = []
            self.y_list = []

    def zero_track(self):
        self.x_list = [0]
        self.y_list = []

