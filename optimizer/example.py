import math
import optim

for x in range(100):
    y = optim.log(x, math.sin(x/20), name='s')
