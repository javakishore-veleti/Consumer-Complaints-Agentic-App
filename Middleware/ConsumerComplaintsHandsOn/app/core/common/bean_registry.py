"""Shared bean registry for package objects_factory init() (DESIGN.md D45)."""

from __future__ import annotations

import threading


class DuplicateBeanError(ValueError):
    pass


class BeanNotFoundError(LookupError):
    pass


class BeanAmbiguousError(LookupError):
    pass


class BeanRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_interface: dict[type, list[object]] = {}

    def register(self, interface: type, instance: object) -> None:
        with self._lock:
            existing = self._by_interface.setdefault(interface, [])
            for bean in existing:
                if bean is instance:
                    raise DuplicateBeanError(
                        f"{interface!r} already has this instance registered"
                    )
            existing.append(instance)

    def get_one(self, interface: type) -> object:
        with self._lock:
            beans = self._by_interface.get(interface, [])
            if not beans:
                raise BeanNotFoundError(f"no bean registered for {interface!r}")
            if len(beans) > 1:
                raise BeanAmbiguousError(
                    f"expected one bean for {interface!r}, found {len(beans)}"
                )
            return beans[0]

    def get_all(self, interface: type) -> list[object]:
        with self._lock:
            return list(self._by_interface.get(interface, []))


bean_registry = BeanRegistry()
