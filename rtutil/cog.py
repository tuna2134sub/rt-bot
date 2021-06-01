# RT - Cog

import inspect


class CogMeta(type):
    def __new__(cls, name, bases, attrs):
        super().__init__(cls, name, bases, attrs)
        return cls


class Cog(metaclass=CogMeta):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)

        return self

    def listener(self, name=None):
        def decorator(function):
            if not inspect.iscoroutine(function):
                raise TypeError("登録する関数はコルーチンにする必要があります。")
            function.__listener = function.__name__
            return function
        return decorator
