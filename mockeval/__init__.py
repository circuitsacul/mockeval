class Mock:
    def __init__(self, name):
        self._name = name

    def __mul__(self, other):
        return MockMul(self, other)
    __rmul__ = __mul__

    def __truediv__(self, other):
        return MockDiv(self, other)

    def __rtruediv__(self, other):
        return MockDiv(other, self)

    def __floordiv__(self, other):
        return (self / other).map(int)

    def __rfloordiv__(self, other):
        return (other / self).map(int)

    def __pow__(self, power):
        return MockPower(self, power)

    def __rpow__(self, value):
        return MockPower(value, self)

    def __getattr__(self, key):
        return MockGet(self, key)

    def __call__(self, *args, **kwargs):
        return MockCall(self, args, kwargs)

    def map(self, func):
        return MockCall(func, [self], {})


class MockValue(Mock):
    def __init__(self, value):
        self._value = value


class MockCall(Mock):
    def __init__(self, func, args, kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs


class MockMul(Mock):
    def __init__(self, left, right):
        self._left = left
        self._right = right


class MockDiv(Mock):
    def __init__(self, left, right):
        self._left = left
        self._right = right


class MockPower(Mock):
    def __init__(self, value, power):
        self._value = value
        self._power = power


class MockGet(Mock):
    def __init__(self, value, key):
        self._value = value
        self._key = key


class MockGetter:
    def __getattr__(self, name):
        return Mock(name)


_ = MockGetter()


def meval(mock, **values):
    if not isinstance(mock, Mock):
        if isinstance(mock, dict):
            return {meval(k, **values): meval(v, **values) for k, v in mock.items()}
        if isinstance(mock, list):
            return [meval(arg, **values) for arg in mock]
        if isinstance(mock, tuple):
            return tuple([meval(arg, **values) for arg in mock])
        return mock

    t = type(mock)
    if t is Mock:
        return values.get(mock._name, mock)
    if t is MockValue:
        return meval(mock._value, **values)
    if t is MockMul:
        return meval(mock._left, **values) * meval(mock._right, **values)
    if t is MockDiv:
        return meval(mock._left, **values) / meval(mock._right, **values)
    if t is MockPower:
        return meval(mock._value, **values) ** meval(mock._power, **values)
    if t is MockGet:
        return getattr(meval(mock._value, **values), mock._key)
    if t is MockCall:
        args = [meval(arg, **values) for arg in mock._args]
        kwargs = {meval(k, **values): meval(v, **values)
                  for k, v in mock._kwargs.items()}
        func = meval(mock._func, **values)
        return func(*args, **kwargs)
