"""Singleton support for every class in api, facades, services and dao.

Put `metaclass=SingletonMeta` on an interface. Every implementation then inherits it, so calling
`SomeImpl()` any number of times, from any thread, always returns the same object. Interfaces that use
abstract methods keep working because SingletonMeta is an ABCMeta.

Because one object serves every request, these classes must hold no per-request state. Request state lives
in the ctx. (Req / Resp / Ctx classes, ORM table classes and API request bodies are data, not singletons.)
"""

import threading
from abc import ABCMeta


class SingletonMeta(ABCMeta):
    _instances: dict[type, object] = {}
    _lock = threading.RLock()  # re-entrant: a singleton may build other singletons in its constructor

    def __call__(cls, *args, **kwargs):
        instance = SingletonMeta._instances.get(cls)
        if instance is None:
            with SingletonMeta._lock:
                instance = SingletonMeta._instances.get(cls)
                if instance is None:
                    instance = super().__call__(*args, **kwargs)
                    SingletonMeta._instances[cls] = instance
        return instance
