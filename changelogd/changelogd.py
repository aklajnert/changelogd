# -*- coding: utf-8 -*-
"""Main module."""
import datetime
import getpass
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
from changelogd.utils import get_git_data

from .config import Config

yaml.add_representer(defaultdict, Representer.represent_dict)


class EntryField:
    name: str
    verbose_name: str
    type: str
    required: bool
    multiple: bool

    def __init__(self, **data: typing.Dict[str, typing.Any]) -> None:
        self.name = str(data.get("name"))
        self.verbose_name = str(data.get("verbose_name", ""))
        self.type = str(data.get("type", "str"))
        self.required = bool(data.get("required", True))
        self.multiple = bool(data.get("multiple", False))

    @property
    def value(self) -> typing.Any:
        value = None
        while value is None:
            modifiers = []
            if self.required:
                modifiers.append("required")
            if self.multiple:
                modifiers.append("separate multiple values with comma")
            aux = f" ({', '.join(modifiers)})" if modifiers else ""
            value = input(f"{self.verbose_name}{aux}: ") or None
            if value is None and not self.required:
                break
        if value is not None and self.multiple:
            value = value.split(",")
        return value


def _is_int(input: typing.Any) -> bool:
    try:
        int(input)
        return True
    except (ValueError, TypeError):
        return False


def entry(config: Config, options: typing.Dict[str, typing.Optional[str]]) -> None:
    data = config.get_data()
    entry_fields = [EntryField(**entry) for entry in data.get("entry_fields", [])]
    entry_type = _get_entry_type(data, options)

    entry = {
        entry_.name: options.get(entry_.name) or entry_.value for entry_ in entry_fields
    }
    entry["type"] = entry_type

    entry["os_user"] = getpass.getuser()
    git_data = get_git_data()
    if git_data:
        entry["git_user"], entry["git_email"] = git_data

    hash = hashlib.md5()
    entries_flat = " ".join(f"{key}={value}" for key, value in entry.items())
    hash.update(entries_flat.encode())

    output_file = config.path / f"{entry_type}.{hash.hexdigest()[:8]}.entry.yaml"
    with output_file.open("w") as output_fh:
        yaml.dump(entry, output_fh)

    logging.warning(f"Created changelog entry at {output_file.absolute()}")


def _get_entry_type(
    data: typing.Dict[str, typing.Any], options: typing.Dict[str, typing.Any]
) -> str:
    message_types = data.get("message_types", [])

    provided_type: typing.Union[int, str, None] = options.get("type")
    if provided_type is not None:
        if _is_int(provided_type):
            if not _is_in_range(int(provided_type), message_types):
                sys.exit(
                    f"Given --type has to be positive number, "
                    f"lower than {len(message_types) + 1}"
                )
            return _get_type_name(message_types, provided_type)
        elif isinstance(provided_type, str):
            type_names = {type_.get("name") for type_ in message_types}
            if provided_type not in type_names:
                sys.exit(
                    f"No such type: '{provided_type}'. "
                    f"Available types: {', '.join(type_names)}"
                )
            return provided_type
        else:
            raise TypeError

    for i, message_type in enumerate(message_types):
        print(f"\t[{i + 1}]: {message_type.get('name')}")
    selection = None
    while not _is_int(selection) or not (
        _is_in_range(selection, message_types)  # type: ignore
    ):
        if selection is not None:
            print(
                f"Pick a positive number lower than {len(message_types) + 1}",
                file=sys.stderr,
            )
        selection = input("Select message type [1]: ") or 1
    entry_type = _get_type_name(message_types, selection)  # type: ignore
    return entry_type


def _get_type_name(
    message_types: typing.List[typing.Dict[str, typing.Any]],
    selection: typing.Union[int, str],
) -> str:
    return message_types[int(selection) - 1].get("name", "")


def _is_in_range(
    index: int, message_types: typing.List[typing.Dict[str, typing.Any]]
) -> bool:
    return 0 < int(index) < len(message_types) + 1


def draft(config: Config, version: str) -> None:
    releases, _ = _read_input_files(config, version)

    resolver = Resolver(config)
    draft = resolver.full_resolve(releases)

    print(draft)


def release(config: Config, version: str, check: bool = False) -> None:
    releases, entries = _read_input_files(config, version, check)

    if not config.get_bool_setting("partial"):
        _save_release_file(config, releases, version)
        logging.info("Removing old entry files")
        for entry in entries:
            os.remove(entry)

    resolver = Resolver(config)
    release = resolver.full_resolve(releases)

    if check:
        with config.output_path.open("r") as output_fh:
            previous_content = output_fh.read()

    with config.output_path.open("w") as output_fh:
        output_fh.truncate(0)
        output_fh.write(release)
        logging.info(f"Generated changelog file to {config.output_path}")

    if check and previous_content != release:
        logging.error("Output file content is different than before.")
        sys.exit(1)


def _save_release_file(
    config: Config, releases: typing.List[typing.Dict[str, typing.Any]], version: str
) -> None:
    current_release = releases[0]
    release_id = releases[1]["id"] + 1 if len(releases) > 1 else 0
    output_release_path = config.releases_dir / f"{release_id}.{version}.yaml"
    with output_release_path.open("w") as output_release_fh:
        yaml.dump(current_release, output_release_fh)
        logging.warning(f"Saved new release data into {output_release_path}")


def _read_input_files(
    config: Config, version: str, is_checking: bool = False
) -> typing.Tuple[typing.List[typing.Dict[str, typing.Any]], typing.List[str]]:
    release, entries = _create_new_release(config, version, is_checking)
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
    if release:
        release["previous-release"] = previous_release
        releases.append(release)
    return list(reversed(releases))


def _create_new_release(
    config: Config, version: str, is_checking: bool
) -> typing.Tuple[typing.Dict[str, typing.Any], typing.List[str]]:
    empty = config.get_bool_setting("empty")
    partial = config.get_bool_setting("partial")
    entries = glob.glob(str(config.path.absolute() / "*.entry.yaml"))
    if not entries and not partial and not empty:
        logging.error("Cannot create new release without any entries.")
        sys.exit(1)
    date = datetime.date.today()
    if partial and is_checking:
        date = _get_partial_timestamp(config, entries)
    release: typing.Dict[str, typing.Any] = {
        "entries": defaultdict(list),
        "release_version": version,
        "release_date": date.strftime("%Y-%m-%d"),
        "release_description": input("Release description (hit ENTER to omit): ")
        if not partial
        else None,
    }

    for entry in _sort_entries(entries):
        with open(entry) as entry_file:
            entry_data = yaml.full_load(entry_file)
        release["entries"][entry_data.pop("type")].append(entry_data)
    if not entries and not empty:
        return {}, []
    return release, entries


def _sort_entries(entries: typing.List[str]) -> typing.Iterator[str]:
    with_timestamp = {entry: os.path.getmtime(entry) for entry in entries}
    return reversed(
        [item[0] for item in sorted(with_timestamp.items(), key=lambda x: x[1])]
    )


def _get_partial_timestamp(
    config: Config, entries: typing.List[str]
) -> datetime.datetime:
    timestamps = []
    if config.output_path.is_file():
        timestamps.append(os.path.getmtime(config.output_path.as_posix()))
    for entry in entries:
        timestamps.append(os.path.getmtime(entry))
    timestamps.sort()
    if not timestamps:
        return datetime.datetime.today()
    return datetime.datetime.fromtimestamp(timestamps[-1])
