# -*- coding: utf-8 -*-
"""Main module."""

from .config import Config


class EntryField:
    name: str
    type: str
    required: bool

    def __init__(self, **data):
        self.name = data.get("name")
        self.type = data.get("type", "str")
        self.required = data.get("required", True)


def create_entry(config: Config):
    config.load()
    entry_fields = [EntryField(**entry) for entry in config.data.get("entry-fields")]
