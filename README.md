# mockeval
Cursed lambdas because yes.

## Usage
```py
from mockeval import var, val

times2 = var.x * 2
print(times2.evl(x=2))  # 4

list_with_unkowns = val([1, 2, var.third, var.fourth])
print(list_with_unkowns.evl(third=3, fourth=4))  # [1, 2, 3, 4]

print(list_with_unkowns.map(sum).evl(third=3, fourth=4))  # 10
```

## Why?
yes.
