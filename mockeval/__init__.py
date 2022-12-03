__all__ = ("var", "val")


class MockOp:
    def __init__(self, math_func, inst=None):
        self.math_func = math_func
        self.inst = inst

    def __get__(self, inst, cls):
        if not inst:
            return self

        return MockOp(self.math_func, inst)

    def __call__(self, *args, **kwargs):
        assert self.inst
        return MockGet(self.inst, self.math_func)(*args, **kwargs)


OPS = [
    "mul",
    "truediv",
    "rtruediv",
    "floordiv",
    "rfloordiv",
    "pow",
    "rpow",
    "add",
    "radd",
    "getitem",
]


class Mock:
    def __init__(self, name):
        self._name = name

    def __call__(self, *args, **kwargs):
        return MockCall(self, args, kwargs)

    def __getattr__(self, key):
        return MockGet(self, key)

    def setattr(self, key, val):
        def _setattr(inst, key, val):
            setattr(inst, key, val)
            return inst

        return MockCall(_setattr, [self, key, val], {})

    def setitem(self, key, val):
        def _setitem(inst, key, val):
            inst[key] = val
            return inst

        return MockCall(_setitem, [self, key, val], {})

    def map(self, func):
        return MockCall(func, [self], {})

    def evl(self, **values):
        return evl(self, **values)


for op in OPS:
    name = f"__{op}__"
    setattr(Mock, name, MockOp(name))


class MockValue(Mock):
    def __init__(self, value):
        self._value = value


val = MockValue


class MockCall(Mock):
    def __init__(self, func, args, kwargs, known_values=None):
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


var = MockGetter()


class MissingValue(Exception):
    pass


def evl(mock, allow_missing=True, /, **values):
    if not isinstance(mock, Mock):
        if isinstance(mock, dict):
            return {
                evl(k, allow_missing, **values): evl(
                    v, allow_missing, **values
                )
                for k, v in mock.items()
            }
        if isinstance(mock, list):
            return [evl(arg, allow_missing, **values) for arg in mock]
        if isinstance(mock, tuple):
            return tuple([evl(arg, allow_missing, **values) for arg in mock])
        return mock

    t = type(mock)
    if t is Mock:
        if not allow_missing and mock._name not in values:
            raise MissingValue
        return values.get(mock._name, mock)
    if t is MockValue:
        return evl(mock._value, allow_missing, **values)
    if t is MockGet:
        return getattr(evl(mock._value, allow_missing, **values), mock._key)
    if t is MockCall:
        values = values.copy()
        values.update(mock._known_values)
        try:
            args = [evl(arg, False, **values) for arg in mock._args]
            kwargs = {
                evl(k, False, **values): evl(v, False, **values)
                for k, v in mock._kwargs.items()
            }
        except MissingValue:
            mock._known_values = values
            return mock
        func = evl(mock._func, allow_missing, **values)
        return func(*args, **kwargs)
