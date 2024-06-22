For Development use these magic functions:

```
%load_ext autoreload 
%autoreload2 magic
```

list mode xy:

```
import tracker
x = [i for i in range(1000)]
y = [math.sin(i) for i in range(1000)]
tracker.xy().push(x,y)
```

list mode log:

```
import tracker
y = [math.sin(i) for i in range(1000)]
tracker.log().push(y)
```

Numpy arrays should be converted to a list:

```
tracker_1 = tracker.log()
tracker_1.push(np.arange(1000).tolist())
```
