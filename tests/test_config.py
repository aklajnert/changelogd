from pathlib import Path

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
