import configparser
import logging
import sys
import typing
from pathlib import Path

import click
import toml
import yaml

DEFAULT_PATH = Path() / "changelog.d"
DEFAULT_CONFIG = {
    "message-types": [
        {"name": "feature", "title": "Features"},
        {"name": "bug", "title": "Bug fixes"},
        {"name": "doc", "title": "Documentation changes"},
        {"name": "deprecation", "title": "Deprecations"},
        {"name": "other", "title": "Other changes"},
    ],
    "templates-dir": "./templates",
    "releases-dir": "./releases",
    "output-file": "../changelog.md",
}


def load_toml(path: Path) -> typing.Optional[str]:
    with path.open() as file_handle:
        config = toml.load(file_handle)

    return config.get("tool", {}).get("changelogd", {}).get("config")


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

SUPPORTED_CONFIG_FILES = [
    (
        Path("pyproject.toml"),
        {"load_function": load_toml, "default": CONFIG_SNIPPET_TOML},
    ),
    (Path("setup.cfg"), {"load_function": load_ini, "default": CONFIG_SNIPPET}),
    (Path("tox.ini"), {"load_function": load_ini, "default": CONFIG_SNIPPET}),
]


class Config:
    def load(self):
        config_path = self._search_config() or DEFAULT_CONFIG
        if not config_path.is_dir():
            sys.exit(
                f"The configuration directory does not exist: "
                f"{config_path.absolute().resolve()}"
            )

        config_file = config_path / "config.yaml"
        if not config_file.is_file():
            sys.exit(
                f"The main configuration file does not exist: "
                f"{config_file.absolute().resolve()}"
            )

        with config_file.open() as config:
            self.config = yaml.full_load(config)

    def _search_config(self) -> typing.Optional[Path]:
        for config_file, file_data in SUPPORTED_CONFIG_FILES:
            config_path = file_data["load_function"](config_file)
            if not config_path.is_file():
                continue

            if config_path:
                logging.info(
                    f"Load configuration from file {config_file.absolute().resolve()}"
                )
                logging.debug(
                    f"Configuration directory: {config_file.absolute().resolve()}"
                )
                return config_path
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

    def init_config(self, path: typing.Optional[str] = None):
        if path is not None:
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

        if path != DEFAULT_PATH:
            config_file, details = next(
                (
                    (config_file, details)
                    for config_file, details in SUPPORTED_CONFIG_FILES
                    if config_file.is_file()
                ),
                (None, None),
            )
            if config_file:
                snippet = details["default"].format(
                    path=output_path.absolute().resolve()
                )
                logging.warning(
                    f"The configuration path is not standard, please add a "
                    f"following snippet to the '{config_file.absolute().resolve()}' "
                    f"file:\n\n{snippet}"
                )
