# -*- coding: utf-8 -*-
"""Main module."""
import datetime
import getpass
import glob
import hashlib
import json
import logging
import os
import re
import sys
import typing
from collections import defaultdict
from pathlib import Path

from ruamel.yaml import YAML  # type: ignore

from .computed_values import ComputedValueProcessor
from .config import Config
from .config import DEFAULT_USER_DATA
from changelogd.resolver import Resolver
from changelogd.utils import add_to_git
from changelogd.utils import get_git_data

yaml = YAML(typ="unsafe")
yaml.default_flow_style = False


class EntryField:
    name: str
    verbose_name: str
    required: bool
    multiple: bool

    def __init__(self, **data: typing.Dict[str, typing.Any]) -> None:
        self.name = str(data.get("name", ""))
        if not self.name:
            logging.error("Each 'entry_fields' element needs to have 'name'.")
            sys.exit(1)
        if " " in self.name:
            logging.error(
                "The 'name' argument of an 'entry_fields' element cannot contain spaces."
            )
            sys.exit(1)
        self.verbose_name = str(data.get("verbose_name", ""))
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
            value = input(f"{self.verbose_name or self.name}{aux}: ") or None
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
    computed_value_processors = [
        ComputedValueProcessor(item) for item in data.get("computed_values", [])
    ]
    entry_fields = [EntryField(**entry) for entry in data.get("entry_fields", [])]
    entry_type = _get_entry_type(data, options)

    entry = {
        entry_.name: options.get(entry_.name) or entry_.value for entry_ in entry_fields
    }
    entry["type"] = entry_type

    _add_user_data(entry, config.get_value("user_data", DEFAULT_USER_DATA))

    if computed_value_processors:
        for processor in computed_value_processors:
            entry.update(processor.get_data())

    hash = hashlib.md5()
    entries_flat = " ".join(f"{key}={value}" for key, value in entry.items())
    hash.update(entries_flat.encode())

    entry["timestamp"] = int(datetime.datetime.now().timestamp())
    output_file = config.path / f"{entry_type}.{hash.hexdigest()[:8]}.entry.yaml"
    with output_file.open("w") as output_fh:
        yaml.dump(entry, output_fh)
    add_to_git(output_file)

    logging.warning(f"Created changelog entry at {output_file.absolute()}")


def _add_user_data(
    entry: dict, user_data: typing.Union[typing.List[str], None]
) -> None:
    if not user_data:
        return
    data = {}
    data["os_user"] = getpass.getuser()
    git_data = get_git_data()
    if git_data:
        data["git_user"], data["git_email"] = git_data

    for key in user_data:
        source, destination, *_ = key.split(":", maxsplit=1) * 2

        if source not in DEFAULT_USER_DATA:
            sys.exit(
                f"The '{source}' variable is not supported in 'user_data'. "
                f"Available choices are: '{', '.join(DEFAULT_USER_DATA)}'."
            )

        entry[destination] = data[source]


def _get_entry_type(
    data: typing.Dict[str, typing.Any], options: typing.Dict[str, typing.Any]
) -> str:
    message_types = data.get("message_types", [])
    if not message_types:
        logging.error("The 'message_types' field is missing from the configuration")
        sys.exit(1)

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
        print(f"\t[{i + 1}]: {message_type.get('title')} [{message_type.get('name')}]")
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


def release(
    version: typing.Optional[str] = None,
    check: bool = False,
    partial: bool = False,
    output: str = "",
    config: typing.Union[Config, str, None] = None,
) -> None:
    if config is None:
        config = Config()
    elif not isinstance(config, Config):
        config = Config(config)
    config.settings["partial"] = partial
    if version is None:
        version = config.partial_name
    releases, entries = _read_input_files(config, version, check)

    if not config.get_bool_setting("partial"):
        _save_release_file(config, releases, version)
        logging.info("Removing old entry files")
        for entry in entries:
            os.remove(entry)

    resolver = Resolver(config)
    release = resolver.full_resolve(releases)

    output_path = Path(output) if output else config.output_path

    if check:
        with output_path.open("r") as output_fh:
            previous_content = output_fh.read()

    with output_path.open("w") as output_fh:
        output_fh.truncate(0)
        output_fh.write(release)
        logging.warning(f"Generated changelog file to {output_path}")

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
    add_to_git(output_release_path)


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
            release_item = yaml.load(release_fh)
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
        release["previous_release"] = previous_release
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

    _grab_entries(entries, release)

    for group_name, items in release["entries"].items():
        release["entries"][group_name] = list(_sort_entries(items))

    # normalize release by dumping and loading it back via JSON
    release = json.loads(json.dumps(release))
    if not entries and not empty:
        return {}, []
    return release, entries


def _grab_entries(
    entries: typing.List[str], release: typing.Dict[str, typing.Any]
) -> None:
    for entry_path in entries:
        with open(entry_path) as entry_file:
            entry_data = yaml.load(entry_file)
        timestamp = entry_data.get("timestamp") or os.path.getmtime(entry_path)
        entry_data["timestamp"] = timestamp
        release["entries"][entry_data.pop("type")].append(entry_data)


def _sort_entries(items: typing.List[typing.Dict]) -> typing.Iterator[typing.Dict]:
    return reversed(sorted(items, key=lambda x: (x["timestamp"])))  # type: ignore


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
