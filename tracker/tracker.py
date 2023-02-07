import requests as rq

host = "http://localhost:5005/api/loss_charting"
session = rq.Session()

class log:
    x_list = []
    y_list = []
    def __init__(self, x, y, name='first'):
        self.post(x, y, name)

    def post(self, x, y, name, host="http://localhost:5005/api/loss_charting"):
        print('log')
        print(len(self.x_list))

        if type(x) == list:
            self.x_list.extend(x)
            self.y_list.extend(y)
        else:
            self.x_list.extend([x])
            self.y_list.extend([y])
        if len(self.x_list) % 1000 == 0:
            print('passed if')
            session.post(host, json={"yCoordinates": self.y_list, 'xCoordinates': self.x_list, 'name': name})
            print(len(self.x_list))
            log.x_list = []
            log.y_list = []


