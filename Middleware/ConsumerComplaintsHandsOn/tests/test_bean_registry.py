"""D45: shared bean registry — one instance, or a list in registration order."""

import pytest

from app.core.common.bean_registry import (
    BeanAmbiguousError,
    BeanNotFoundError,
    BeanRegistry,
    DuplicateBeanError,
)


class Animal:
    pass


class Dog(Animal):
    pass


class Cat(Animal):
    pass


def test_get_one_returns_the_only_instance():
    reg = BeanRegistry()
    dog = Dog()
    reg.register(Animal, dog)
    assert reg.get_one(Animal) is dog


def test_get_all_preserves_registration_order():
    reg = BeanRegistry()
    a, b = Dog(), Cat()
    reg.register(Animal, a)
    reg.register(Animal, b)
    assert reg.get_all(Animal) == [a, b]


def test_get_one_raises_when_none_or_several():
    reg = BeanRegistry()
    with pytest.raises(BeanNotFoundError):
        reg.get_one(Animal)
    reg.register(Animal, Dog())
    reg.register(Animal, Cat())
    with pytest.raises(BeanAmbiguousError):
        reg.get_one(Animal)


def test_duplicate_same_instance_raises():
    reg = BeanRegistry()
    dog = Dog()
    reg.register(Animal, dog)
    with pytest.raises(DuplicateBeanError):
        reg.register(Animal, dog)


def test_get_all_empty_when_unregistered():
    assert BeanRegistry().get_all(Animal) == []
