# -*- coding: utf-8 -*-
"""Main module."""
import glob
import hashlib
import logging
import sys
import typing

import yaml

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
    entry_type = message_types[int(selection) - 1].get("name")
    entries["type"] = entry_type

    hash = hashlib.md5()
    entries_flat = " ".join(f"{key}={value}" for key, value in entries.items())
    hash.update(entries_flat.encode())

    output_file = config.path / f"{entry_type}.{hash.hexdigest()[:8]}.entry.yaml"
    with output_file.open("w") as output_fh:
        yaml.dump(entries, output_fh)

    logging.warning(f"Created changelog entry at {output_file.absolute()}")


def prepare_draft(config):
    config.load()
    entries = glob.glob(str(config.path.absolute() / "*.entry.yaml"))
    print(entries)
