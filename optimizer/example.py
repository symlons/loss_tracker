#!/usr/bin/env python

import math
import optim

for x in range(1000):
    #y = optim.log(x, math.sin(x/20), name='1')
    z = optim.log(x, math.sin(x/10), name='2')
