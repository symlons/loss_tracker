#!/usr/bin/env python

import math
import tracker

for x in range(1000):
    y = tracker.log(x, math.sin(x/80), name='1')
    #z = optim.log(x, math.sin(x/10), name='2')
