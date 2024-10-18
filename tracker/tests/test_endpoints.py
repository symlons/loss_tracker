import tracker
import math


x = []
y = []

count = 0
iterations = 2000 + 1
x1 = tracker.xy(name='q')
for i in range(iterations):
    x.append(i) 
    y.append(math.sin(i))
    if i % (iterations - 1) == 0:
        print(i)
        count += len(x[i:])
        x1.push(x[:i], y[:i])


x2 = tracker.xy()
for i in range(2000):
    x = [i]
    y = [math.sin(i)]
    x2.push(x, y)


x2 = tracker.xy()
for i in range(2000):
    x = [i]
    y = [math.sin(i)]
    x2.push(x, y)


from tracker import log
import math
import random


x3 = tracker.xy(name='5')
for i in range(10000):
    x3.push(i, random.gauss(0.1, 0.5)*10)
x3.zero_track()


import math
import random

x4 = tracker.xy(name='7')
for i in range(100000):
    x4.push(i, random.gauss(0.1, 0.5))
x4.zero_track()



import random
import tracker
import numpy as np


t1 = tracker.log(name='r')
for i in range(500):
    t1.push(i)
t1.zero_track()



t2 = tracker.log(name='b')
for i in range(1000):
    t2.push(i**2)


t3 = tracker.log(name='u')
for i in range(1000):
    t3.push(i**1.5)
t3.zero_track()


t4 = tracker.xy(name='b')


t4.push(np.arange(1000).tolist(), np.arange(1000).tolist())


t4 = tracker.log(name='b')
t4.push(np.arange(1000).tolist())
