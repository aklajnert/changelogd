import builtins
import functools
import getpass
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest_subprocess import FakeProcess
from ruamel.yaml import YAML

from changelogd import changelogd
from changelogd.config import Config

yaml = YAML()


def fake_yaml_dump(data, _, namespace):
    namespace.data = data


def test_missing_type(monkeypatch, fp: FakeProcess, fs):
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- name: test\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)

    with pytest.raises(
        SystemExit,
        match="Missing `type` for computed value: {'name': 'test'}",
    ):
        changelogd.entry(config, {})


def test_invalid_type(monkeypatch, fp: FakeProcess, fs):
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: invalid\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)

    with pytest.raises(
        SystemExit,
        match=(
            "Unavailable type: 'invalid'. Available types: "
            "local_branch_name remote_branch_name branch_name"
        ),
    ):
        changelogd.entry(config, {})


def test_basic_data(monkeypatch, fp: FakeProcess, fs):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: branch_name\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout="local_branch_name"
    )
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        stdout="remote_branch_name",
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "branch_name": "local_branch_name - remote_branch_name",
    }


@pytest.mark.parametrize(
    "branches",
    [
        ("fixing task JIRA-1234", "remote_branch_name"),
        ("local_branch_name", "fixing task JIRA-1234"),
    ],
)
def test_matching_regex(monkeypatch, fp: FakeProcess, fs, branches):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: branch_name\n"
            "  regex: '(?P<value>JIRA-\d+)'\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    local_branch_name, remote_branch_name = branches
    fp.register(["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=local_branch_name)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        stdout=remote_branch_name,
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "branch_name": "JIRA-1234",
    }


def test_not_matching_regex(monkeypatch, fp: FakeProcess, fs, caplog):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: local_branch_name\n"
            "  regex: '(?P<value>JIRA-\d+)'\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout="local_branch_name"
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "local_branch_name": None,
    }
    assert (
        caplog.messages[0]
        == "The regex '(?P<value>JIRA-\\d+)' didn't match 'local_branch_name'."
    )


def test_subprocess_failure(monkeypatch, fp: FakeProcess, fs, caplog):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: branch_name\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    fp.register(["git", "rev-parse", "--abbrev-ref", "HEAD"], returncode=128)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        returncode=128,
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "branch_name": None,
    }
    assert (
        caplog.messages[0]
        == "Failed to run 'git rev-parse --abbrev-ref HEAD' to get local branch name"
    )
    assert caplog.messages[2] == (
        "Failed to run 'git rev-parse --abbrev-ref --symbolic-full-name @{u}' "
        "to get remote branch name"
    )


def test_default_value(monkeypatch, fp: FakeProcess, fs, caplog):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: branch_name\n"
            "  default: default_name\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    fp.register(["git", "rev-parse", "--abbrev-ref", "HEAD"], returncode=128)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        returncode=128,
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "branch_name": "default_name",
    }


def test_default_not_matching_regex(monkeypatch, fp: FakeProcess, fs, caplog):
    namespace = SimpleNamespace()
    config_path = Path("/fake/path/to/changelog.d")
    fs.create_file(
        config_path / "config.yaml",
        contents=(
            "message_types:\n"
            "- name: feature\n"
            "  title: Features\n"
            "computed_values:\n"
            "- type: local_branch_name\n"
            "  default: default_name\n"
            "  regex: '(?P<value>JIRA-\d+)'\n"
            "user_data: null\n"
        ),
    )
    config = Config(config_path)
    fp.register(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout="local_branch_name"
    )
    fp.register(["git", "add", fp.any()])
    fp.keep_last_process(True)

    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "type": "feature",
        "local_branch_name": "default_name",
    }
    assert (
        caplog.messages[0]
        == "The regex '(?P<value>JIRA-\\d+)' didn't match 'local_branch_name'."
    )
