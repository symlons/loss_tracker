import requests as rq

host = "http://localhost:5004/api/loss_charting"
session = rq.Session()


def log(x, y,name='first', host="http://localhost:5004/api/loss_charting"):
    session.post(host, json={"yCoordinates": y, 'xCoordinates': x, 'name': name})


