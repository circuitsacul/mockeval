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
        return MockCall(func, [self], {}, None)

    def meval(self, **values):
        return meval(self, **values)


for op in OPS:
    name = f"__{op}__"
    setattr(Mock, name, MockOp(name))


class MockValue(Mock):
    def __init__(self, value):
        self._value = value


class MockCall(Mock):
    def __init__(self, func, args, kwargs, known_values):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._known_values = known_values or {}


class MockGet(Mock):
    def __init__(self, value, key):
        self._value = value
        self._key = key


class MockGetter:
    def __getattr__(self, name):
        return Mock(name)


_ = MockGetter()


class MissingValue(Exception):
    pass


def meval(mock, allow_missing=True, /, **values):
    if not isinstance(mock, Mock):
        if isinstance(mock, dict):
            return {
                meval(k, allow_missing, **values): meval(v, allow_missing, **values)
                for k, v in mock.items()
            }
        if isinstance(mock, list):
            return [meval(arg, allow_missing, **values) for arg in mock]
        if isinstance(mock, tuple):
            return tuple([meval(arg, allow_missing, **values) for arg in mock])
        return mock

    t = type(mock)
    if t is Mock:
        if not allow_missing and mock._name not in values:
            raise MissingValue
        return values.get(mock._name, mock)
    if t is MockValue:
        return meval(mock._value, allow_missing, **values)
    if t is MockGet:
        return getattr(meval(mock._value, allow_missing, **values), mock._key)
    if t is MockCall:
        values = values.copy()
        values.update(mock._known_values)
        try:
            args = [meval(arg, False, **values) for arg in mock._args]
            kwargs = {
                meval(k, False, **values): meval(v, False, **values)
                for k, v in mock._kwargs.items()
            }
        except MissingValue:
            mock._known_values = values
            return mock
        func = meval(mock._func, allow_missing, **values)
        return func(*args, **kwargs)
