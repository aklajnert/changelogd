import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from changelogd import commands
from changelogd import config


def test_load_toml(fs):
    fs.create_file(
        "pyproject.toml",
        contents=config.CONFIG_SNIPPET_TOML.format(path="/config/path"),
    )
    assert config.load_toml(Path("pyproject.toml")) == "/config/path"

    fs.create_file(
        "pyproject2.toml", contents="[tool.other_tool]\nconfig = '/config/path'"
    )
    assert config.load_toml(Path("pyproject2.toml")) is None

    fs.create_file(
        "pyproject3.toml", contents="[tool.changelogd]\nother_option = '/config/path'"
    )
    assert config.load_toml(Path("pyproject3.toml")) is None


def test_load_ini(fs):
    fs.create_file(
        "config.ini", contents=config.CONFIG_SNIPPET.format(path="/config/path")
    )
    assert config.load_ini(Path("config.ini")) == "/config/path"

    fs.create_file("config2.ini", contents="[tool:other_tool]\nconfig=/config/path")
    assert config.load_ini(Path("config2.ini")) is None

    fs.create_file(
        "config3.ini", contents="[tool:changelogd]\nother_option=/config/path"
    )
    assert config.load_ini(Path("config3.ini")) is None


def test_init_config(fs, caplog, monkeypatch):
    # remove `setup.cfg` and `tox.ini` from supported files,
    # to make tests pass on azure pipelines
    monkeypatch.setattr(
        config, "SUPPORTED_CONFIG_FILES", (config.SUPPORTED_CONFIG_FILES[0],),
    )

    fs.create_dir("/test")
    fs.add_real_directory((Path(__file__).parents[1] / "changelogd" / "templates"))

    runner = CliRunner()
    result = runner.invoke(commands.init, "--path=/test/changelog.d")
    assert result.exit_code == 0

    assert os.listdir("/test") == ["changelog.d"]
    assert sorted(os.listdir("/test/changelog.d")) == [
        "config.yaml",
        "releases",
        "templates",
    ]
    assert sorted(os.listdir("/test/changelog.d/templates")) == [
        "entry.md",
        "main.md",
        "release.md",
    ]
    assert os.listdir("/test/changelog.d/releases") == [".gitkeep"]

    assert all(record.levelname == "WARNING" for record in caplog.records)

    messages = [record.message for record in caplog.records]
    assert messages[0].startswith("Created main configuration file: ")
    assert messages[1].startswith("Copied templates to ")
    assert messages[2].startswith(
        "No configuration file found. Create a pyproject.toml file in root of your "
        "directory, with the following content:"
    )

    result = runner.invoke(commands.init, "--path=/test/changelog.d", input="n")
    assert result.exit_code == 1


def test_custom_path(fs):
    # directory doesn't exist at all
    with pytest.raises(SystemExit) as exc:
        config.Config("/test")

    assert str(exc.value) == "The given configuration path doesn't exist."

    # the path is file, not a directory
    fs.create_file("/config.yaml")
    with pytest.raises(SystemExit) as exc:
        config.Config("/config.yaml")

    assert str(exc.value) == "The configuration path has to be a directory."

    # the config.yaml is missing from the directory
    fs.create_dir("/config_dir")
    with pytest.raises(SystemExit) as exc:
        config.Config("/config_dir")

    assert (
        str(exc.value) == "The 'config.yaml' file doesn't exist in provided directory."
    )

    # all good now
    fs.create_file("/config_dir/config.yaml")
    instance = config.Config("/config_dir")

    assert str(instance.path) == f"{os.sep}config_dir"
