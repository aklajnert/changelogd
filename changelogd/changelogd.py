# -*- coding: utf-8 -*-
"""Main module."""
import datetime
import glob
import hashlib
import logging
import os
import re
import sys
import typing
from collections import defaultdict
from pathlib import Path

import yaml
from yaml.representer import Representer

from changelogd.resolver import Resolver

from .config import Config

yaml.add_representer(defaultdict, Representer.represent_dict)


class EntryField:
    name: str
    verbose_name: str
    type: str
    required: bool

    def __init__(self, **data: typing.Dict[str, typing.Any]) -> None:
        self.name = str(data.get("name"))
        self.verbose_name = str(data.get("verbose_name", ""))
        self.type = str(data.get("type", "str"))
        self.required = bool(data.get("required", True))

    @property
    def value(self) -> typing.Any:
        value = None
        while value is None:
            value = input(f"{self.verbose_name}: ") or None
            if value is None and not self.required:
                break
        return value


def _is_int(input: typing.Any) -> bool:
    try:
        int(input)
        return True
    except (ValueError, TypeError):
        return False


def entry(config: Config) -> None:
    data = config.get_data()
    entry_fields = [EntryField(**entry) for entry in data.get("entry_fields", [])]
    message_types = data.get("message_types", [])
    for i, message_type in enumerate(message_types):
        print(f"\t[{i + 1}]: {message_type.get('name')}")
    selection = None
    while not _is_int(selection) or not (
        0 < int(selection) < len(message_types) + 1  # type: ignore
    ):
        if selection is not None:
            print(
                f"Pick a positive number lower than {len(message_types) + 1}",
                file=sys.stderr,
            )
        selection = input("Select message type [1]: ") or 1

    entries = {entry.name: entry.value for entry in entry_fields}
    entry_type = message_types[int(selection) - 1].get("name")  # type: ignore
    entries["type"] = entry_type

    hash = hashlib.md5()
    entries_flat = " ".join(f"{key}={value}" for key, value in entries.items())
    hash.update(entries_flat.encode())

    output_file = config.path / f"{entry_type}.{hash.hexdigest()[:8]}.entry.yaml"
    with output_file.open("w") as output_fh:
        yaml.dump(entries, output_fh)

    logging.warning(f"Created changelog entry at {output_file.absolute()}")


def draft(config: Config, version: str) -> None:
    releases, _ = _read_input_files(config, version)

    resolver = Resolver(config)
    draft = resolver.full_resolve(releases)

    print(draft)


def release(config: Config, version: str) -> None:
    releases, entries = _read_input_files(config, version)
    _save_release_file(config, releases, version)


def _save_release_file(config, releases, version):
    current_release = releases[0]
    release_id = releases[1]["id"] + 1 if len(releases) > 1 else 0
    output_release_path = config.releases_dir / f"{release_id}.{version}.yaml"
    with output_release_path.open("w") as output_release_fh:
        yaml.dump(current_release, output_release_fh)
        logging.warning(f"Saved new release data into {output_release_path}")


def _read_input_files(
    config: Config, version: str
) -> typing.Tuple[typing.List[typing.Dict[str, typing.Any]], typing.List[str]]:
    release, entries = _create_new_release(config, version)
    releases = _prepare_releases(release, config.releases_dir)

    return releases, entries


def _prepare_releases(
    release: typing.Dict, releases_dir: Path
) -> typing.List[typing.Dict]:
    versions: typing.Dict[int, Path] = dict()
    for item in os.listdir(releases_dir.as_posix()):
        match = re.match(r"(\d+).*\.ya?ml", item)
        if match:
            version = int(match.group(1))
            if version in versions:
                sys.exit(f"The version {version} is duplicated.")
            versions[version] = releases_dir / match.group(0)
    previous_release = None
    releases = []
    for version in sorted(versions.keys()):
        with versions[version].open() as release_fh:
            release_item = yaml.full_load(release_fh)
            if not release_item:
                logging.error(
                    f"Release file {versions[version]} is corrupted and will be ignored."
                )
                continue
            release_item["previous_release"] = previous_release
            release_item["id"] = version
            previous_release = release_item.get("release_version")
            releases.append(release_item)
    release["previous-release"] = previous_release
    releases.append(release)
    return list(reversed(releases))


def _create_new_release(
    config: Config, version: str
) -> typing.Tuple[typing.Dict[str, typing.Any], typing.List[str]]:
    entries = glob.glob(str(config.path.absolute() / "*.entry.yaml"))
    release: typing.Dict[str, typing.Any] = {
        "entries": defaultdict(list),
        "release_version": version,
        "release_date": datetime.date.today().strftime("%Y-%m-%d"),
        "release_description": input("Release description (hit ENTER to omit): "),
    }
    for entry in sorted(entries):
        with open(entry) as entry_file:
            entry_data = yaml.full_load(entry_file)
        release["entries"][entry_data.pop("type")].append(entry_data)
    return release, entries
