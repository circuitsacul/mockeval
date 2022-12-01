class MockOp:
    def __init__(self, math_func, inst=None):
        self.math_func = math_func
        self.inst = inst

    def __get__(self, inst, cls):
        if not inst:
            return self

        return MockOp(self.math_func, inst)

    def __call__(self, other):
        assert self.inst
        return MockGet(self.inst, self.math_func)(other)

OPS = [
    "mul",
    "truediv",
    "rtruediv",
    "floordiv",
    "rfloordiv",
    "pow",
    "rpow",
]

class Mock:
    def __init__(self, name):
        self._name = name

    def __call__(self, *args, **kwargs):
        return MockCall(self, args, kwargs)

    def __getattr__(self, key):
        return MockGet(self, key)

    def map(self, func):
        return MockCall(func, [self], {})

    def meval(self, **values):
        return meval(self, **values)


for op in OPS:
    name = f"__{op}__"
    setattr(Mock, name, MockOp(name))


class MockValue(Mock):
    def __init__(self, value):
        self._value = value


class MockCall(Mock):
    def __init__(self, func, args, kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs


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
    if t is MockGet:
        return getattr(meval(mock._value, **values), mock._key)
    if t is MockCall:
        args = [meval(arg, **values) for arg in mock._args]
        kwargs = {meval(k, **values): meval(v, **values)
                  for k, v in mock._kwargs.items()}
        func = meval(mock._func, **values)
        return func(*args, **kwargs)
