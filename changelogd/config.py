import configparser
import logging
import os
import shutil
import sys
import typing
from copy import deepcopy
from pathlib import Path

import click
import toml
import yaml

DEFAULT_PATH = Path(os.getcwd()) / "changelog.d"
DEFAULT_CONFIG = {
    "message_types": [
        {"name": "feature", "title": "Features"},
        {"name": "bug", "title": "Bug fixes"},
        {"name": "doc", "title": "Documentation changes"},
        {"name": "deprecation", "title": "Deprecations"},
        {"name": "other", "title": "Other changes"},
    ],
    "entry_fields": [
        {
            "name": "issue_id",
            "verbose_name": "Issue ID",
            "type": "str",
            "required": False,
        },
        {
            "name": "message",
            "verbose_name": "Changelog message",
            "type": "str",
            "required": True,
        },
    ],
    "output_file": "../changelog.md",
    "issues_url": "http://repo/issues",
}


def load_toml(path: Path) -> typing.Optional[str]:
    if not path.is_file():
        return None
    with path.open() as file_handle:
        config = toml.load(file_handle)

    return config.get("tool", {}).get("changelogd", {}).get("config")  # type:ignore


def load_ini(path: Path) -> typing.Optional[str]:
    config = configparser.ConfigParser()
    with path.open() as file_handle:
        config.read_file(file_handle)

    try:
        return config.get("tool:changelogd", "config")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None


CONFIG_SNIPPET = "[tool:changelogd]\nconfig={path}"
CONFIG_SNIPPET_TOML = "[tool.changelogd]\nconfig = '{path}'"

SUPPORTED_CONFIG_FILES: typing.List[typing.Tuple[Path, typing.Callable, str]] = [
    (Path("pyproject.toml"), load_toml, CONFIG_SNIPPET_TOML,),
    (Path("setup.cfg"), load_ini, CONFIG_SNIPPET),
    (Path("tox.ini"), load_ini, CONFIG_SNIPPET),
]


class Config:
    def __init__(self):
        self._load()

    def get_data(self) -> dict:
        return deepcopy(self._data)

    def _load(self) -> None:
        self.path = self._search_config() or DEFAULT_PATH
        if not self.path.is_dir():
            sys.exit(
                f"The configuration directory does not exist: "
                f"{self.path.absolute().resolve()}"
            )

        config_file = self.path / "config.yaml"
        if not config_file.is_file():
            sys.exit(
                f"The main configuration file does not exist: "
                f"{config_file.absolute().resolve()}"
            )

        with config_file.open() as config:
            self._data = yaml.full_load(config)

    def _search_config(self) -> typing.Optional[Path]:
        for config_file, load_function, _ in SUPPORTED_CONFIG_FILES:
            config_path = load_function(config_file)  # type: ignore
            if config_path:
                config_path = Path(config_path)
            if not config_path or not config_path.is_file():
                continue

            if config_path:
                logging.info(
                    f"Load configuration from file {config_file.absolute().resolve()}"
                )
                logging.debug(
                    f"Configuration directory: {config_file.absolute().resolve()}"
                )
                return config_path  # type: ignore
        return None

    @classmethod
    def set_verbosity(
        cls, ctx: click.core.Context, option: click.core.Option, verbose: int
    ) -> None:
        levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(
            level=levels.get(verbose, logging.WARNING),
            format="%(asctime)s - %(message)s",
        )

    def init(self, path: typing.Union[str, Path, None] = None) -> None:
        if isinstance(path, str):
            path = Path(path)

        output_directory = path or DEFAULT_PATH
        if output_directory.is_dir():
            if not click.confirm(
                f"The config directory '{output_directory.absolute().resolve()}' "
                f"already exists. "
                f"Do you want to overwrite the configuration files?"
            ):
                sys.exit("Aborted")
        else:
            output_directory.mkdir()

        output_path = output_directory / "config.yaml"
        with output_path.open("w+") as output_stream:
            yaml.safe_dump(DEFAULT_CONFIG, output_stream)

        if output_path.is_file():
            logging.warning(
                f"Created main configuration file: {output_path.absolute().resolve()}"
            )

        target = output_directory / "templates"
        if target.is_dir():
            shutil.rmtree(target)
        dst = shutil.copytree(Path(__file__).parent / "templates", target)
        if dst:
            logging.warning(f"Copied templates to {dst}")

        if path != DEFAULT_PATH:
            config_file, default = next(
                (
                    (config_file, default)
                    for config_file, _, default in SUPPORTED_CONFIG_FILES
                    if config_file.is_file()
                ),
                (None, None),
            )
            if config_file and default:
                snippet = default.format(path=output_path.absolute().resolve())
                logging.warning(
                    f"The configuration path is not standard, please add a "
                    f"following snippet to the '{config_file.absolute().resolve()}' "
                    f"file:\n\n{snippet}"
                )
            if path and not config_file:
                logging.warning(
                    "No configuration file found. Create a pyproject.toml "
                    "file in root of your directory, with the following content:\n\n"
                    f"{CONFIG_SNIPPET_TOML.format(path=path.absolute())}"
                )

        releases_dir = output_directory / "releases"
        releases_dir.mkdir(exist_ok=True)
        with open(releases_dir / ".gitkeep", "w+"):
            pass
