"""Typed Mongo document wrapper so helpers obey D37 (one object, not a bare dict)."""


class MongoDocument(dict):
    """A MongoDB document. Subclass of dict so call sites stay simple."""
