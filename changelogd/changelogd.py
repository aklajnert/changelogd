# -*- coding: utf-8 -*-
"""Main module."""
import sys
import typing

from .config import Config

SENTINEL = object()


class EntryField:
    name: str
    verbose_name: str
    type: str
    required: bool

    def __init__(self, **data):
        self.name = data.get("name")
        self.verbose_name = data.get("verbose-name")
        self.type = data.get("type", "str")
        self.required = data.get("required", True)
        self._value = SENTINEL

    @property
    def value(self) -> typing.Any:
        value = None
        while value is None:
            value = input(f"{self.verbose_name}: ") or None
            if value is None and not self.required:
                break
        return value


def _is_int(input):
    try:
        int(input)
        return True
    except (ValueError, TypeError):
        return False


def create_entry(config: Config):
    config.load()
    entry_fields = [EntryField(**entry) for entry in config.data.get("entry-fields")]
    message_types = config.data.get("message-types")
    for i, message_type in enumerate(message_types):
        print(f"\t[{i + 1}]: {message_type.get('name')}")
    selection = None
    while not _is_int(selection) or not (0 < int(selection) < len(message_types) + 1):
        if selection is not None:
            print(
                f"Pick a positive number lower than {len(message_types) + 1}",
                file=sys.stderr,
            )
        selection = input("Select message type [1]: ") or 1

    entries = {entry.name: entry.value for entry in entry_fields}
    print(entries)
