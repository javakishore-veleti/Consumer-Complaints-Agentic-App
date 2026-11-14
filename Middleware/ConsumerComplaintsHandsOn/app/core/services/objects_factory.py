"""The only module of the services package that may import from services/impl.

No service exists yet. When one is added: its interface uses `metaclass=SingletonMeta` and a static method here
returns the singleton, typed as the interface.
"""


class ServicesObjectsFactory:
    pass
