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
from ruamel.yaml import YAML  # type: ignore
from ruamel.yaml.comments import CommentedMap  # type: ignore

yaml = YAML()

DEFAULT_PATH = Path(os.getcwd()) / "changelog.d"
DEFAULT_OUTPUT = "../changelog."
PARTIAL_KEY_NAME = "partial_release_name"
DEFAULT_PARTIAL_VALUE = "unreleased"
DEFAULT_USER_DATA = ["os_user", "git_user", "git_email"]
DEFAULT_CONFIG = CommentedMap(
    {
        "entry_fields": [
            {
                "name": "issue_id",
                "verbose_name": "Issue ID",
                "type": "str",
                "required": False,
                "multiple": True,
            },
            {
                "name": "message",
                "verbose_name": "Changelog message",
                "type": "str",
                "required": True,
            },
        ],
        "output_file": DEFAULT_OUTPUT,
        PARTIAL_KEY_NAME: DEFAULT_PARTIAL_VALUE,
        "user_data": DEFAULT_USER_DATA,
    }
)
DEFAULT_CONFIG.insert(
    0,
    "context",
    {"issues_url": "http://repo/issues"},
    comment="All variables defined here will be passed into templates",
)
DEFAULT_CONFIG.insert(
    1,
    "message_types",
    [
        {"name": "feature", "title": "Features"},
        {"name": "bug", "title": "Bug fixes"},
        {"name": "doc", "title": "Documentation changes"},
        {"name": "deprecation", "title": "Deprecations"},
        {"name": "other", "title": "Other changes"},
    ],
    comment="The order defined below will be preserved in the output changelog file",
)


def load_toml(path: Path) -> typing.Optional[str]:
    if not path.is_file():
        return None
    with path.open() as file_handle:
        config = toml.load(file_handle)

    return config.get("tool", {}).get("changelogd", {}).get("config")  # type:ignore


def load_ini(path: Path) -> typing.Optional[str]:
    if not path.is_file():
        return None
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
    (
        Path("pyproject.toml"),
        load_toml,
        CONFIG_SNIPPET_TOML,
    ),
    (Path("setup.cfg"), load_ini, CONFIG_SNIPPET),
    (Path("tox.ini"), load_ini, CONFIG_SNIPPET),
]


class Config:
    settings: typing.Dict[str, typing.Any] = dict()

    def __init__(self, path: typing.Union[Path, str, None] = None) -> None:
        self._path: typing.Optional[Path]
        if path:
            self._path = Path(path) if isinstance(path, str) else path
            if not self._path.exists():
                sys.exit("The given configuration path doesn't exist.")
            if not self._path.is_dir():
                sys.exit("The configuration path has to be a directory.")
            if not (self._path / "config.yaml").is_file():
                sys.exit("The 'config.yaml' file doesn't exist in provided directory.")
        else:
            self._path = None
        self._data: typing.Optional[dict] = None

    def get_context(self) -> typing.Dict[str, typing.Any]:
        return self.get_value("context") or {}

    def get_bool_setting(self, name: str) -> bool:
        return bool(self.settings.get(name))

    @property
    def path(self) -> Path:
        if self._path is None:
            self._path = self._get_path()
        return self._path

    @property
    def releases_dir(self) -> Path:
        return self.path / "releases"

    @property
    def output_path(self) -> Path:
        output_path = self.get_value("output_file", DEFAULT_OUTPUT)
        return Path((self.path / output_path).resolve())

    @property
    def partial_name(self) -> str:
        return str(self.get_value(PARTIAL_KEY_NAME, DEFAULT_PARTIAL_VALUE))

    def get_data(self) -> dict:
        if self._data is None:
            self._data = self._load_data()
        return deepcopy(self._data)

    def get_value(self, key: str, default: typing.Any = None) -> typing.Any:
        return self.get_data().get(key, default)

    def _get_path(self) -> Path:
        path = self._search_config() or DEFAULT_PATH
        if not path.is_dir():
            sys.exit(
                f"The configuration directory does not exist: "
                f"{path.absolute().resolve()}.\n"
                f"Run `changelogd init` to create it."
            )
        return path

    def _load_data(self) -> dict:
        config_file = self.path / "config.yaml"
        if not config_file.is_file():
            sys.exit(
                f"The main configuration file does not exist: "
                f"{config_file.absolute().resolve()}.\n"
                f"Run `changelogd init` to create it."
            )

        with config_file.open() as config:
            return yaml.load(config) or {}

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
            format="%(message)s",
        )

    def init(
        self, path: typing.Union[str, Path, None] = None, format: str = "md"
    ) -> None:
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

        config_data = {**DEFAULT_CONFIG}
        config_data["output_file"] += format

        output_path = output_directory / "config.yaml"
        with output_path.open("w+") as output_stream:
            yaml.dump(config_data, output_stream)

        if output_path.is_file():
            logging.warning(
                f"Created main configuration file: {output_path.absolute().resolve()}"
            )

        shutil.copy(
            Path(__file__).parent / "templates" / "README.md",
            output_directory / "README.md",
        )

        target = output_directory / "templates"
        if target.is_dir():
            shutil.rmtree(target)
        dst = shutil.copytree(Path(__file__).parent / "templates" / format, target)
        if dst:
            logging.warning(f"Copied templates to {dst}")

        if path is not None and path != DEFAULT_PATH:
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
