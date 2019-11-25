import logging
import sys
import typing
from pathlib import Path

import click
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

CONFIG_SNIPPET = "[tool:changelogd]\nconfig={path}"
CONFIG_SNIPPET_TOML = "[tool.changelogd]\nconfig={path}"
SUPPORTED_CONFIG_FILES = [
    (Path("pyproject.toml"), {"format": "toml", "default": CONFIG_SNIPPET_TOML}),
    (Path("setup.cfg"), {"format": "ini", "default": CONFIG_SNIPPET}),
    (Path("tox.ini"), {"format": "ini", "default": CONFIG_SNIPPET}),
]


class Config:
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
                f"The config directory '{output_directory.absolute().resolve()}' already exists. "
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
                    f"The configuration path is not standard, please add a following snippet to "
                    f"the '{config_file.absolute().resolve()}' file:\n\n{snippet}"
                )
