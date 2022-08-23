import builtins
import functools
import getpass
import glob
import importlib
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from changelogd import changelogd
from changelogd import commands
from changelogd.config import Config
from changelogd.config import DEFAULT_CONFIG

yaml = YAML()


class FakeContext:
    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass


class FakePath:
    def __init__(self, *args, **kwargs):
        pass

    def __truediv__(self, other):
        return self

    def open(self, *args, **kwargs):
        return FakeContext()

    def absolute(self):
        return None


def fake_yaml_dump(data, _, namespace):
    namespace.data = data


def test_incorrect_input_entry():
    runner = CliRunner()

    entry = runner.invoke(commands.entry)
    assert entry.exit_code == 1


def test_entry_help(setup_env):
    runner = CliRunner()
    runner.invoke(commands.init)

    # this is required to update the decorators which can be done
    # after initializing configuration
    importlib.reload(commands)

    entry = runner.invoke(
        commands.entry,
        ["--help"],
    )
    assert entry.exit_code == 0
    assert (
        entry.stdout
        == """Usage: entry [OPTIONS]

  Create a new changelog entry.

Options:
  -v, --verbose    Increase verbosity.
  --message TEXT   Changelog message
  --issue-id TEXT  Issue ID
  --type TEXT      Message type (as number or string).
  --help           Show this message and exit.
"""
    )


@pytest.mark.parametrize("type_input", ["1", "feature"])
def test_non_interactive_data(setup_env, type_input):
    runner = CliRunner()
    runner.invoke(commands.init)

    # this is required to update the decorators which can be done
    # after initializing configuration
    importlib.reload(commands)

    entry = runner.invoke(
        commands.entry,
        ["--type", type_input, "--message", "test message", "--issue-id", "100"],
    )
    assert entry.exit_code == 0

    entries = glob.glob(str(setup_env / "changelog.d" / "*entry.yaml"))
    assert len(entries) == 1

    with open(entries[0]) as entry_fh:
        entry_content = yaml.load(entry_fh)

    assert entry_content.pop("timestamp")
    assert entry_content == {
        "git_email": "user@example.com",
        "git_user": "Some User",
        "issue_id": "100",
        "message": "test message",
        "os_user": "test-user",
        "type": "feature",
    }


def test_entry_missing_message_types(setup_env, caplog):
    runner = CliRunner()
    runner.invoke(commands.init)

    with open(setup_env / "changelog.d" / "config.yaml") as config_fh:
        config_content = yaml.load(config_fh)

    config_content.pop("message_types")

    with open(setup_env / "changelog.d" / "config.yaml", "w+") as config_fh:
        yaml.dump(config_content, config_fh)

    caplog.clear()
    entry = runner.invoke(commands.entry)
    assert entry.exit_code == 1
    assert (
        "The 'message_types' field is missing from the configuration" in caplog.messages
    )


def test_entry_incorrect_entry_fields(setup_env, caplog):
    runner = CliRunner()
    runner.invoke(commands.init)

    with open(setup_env / "changelog.d" / "config.yaml") as config_fh:
        config_content = yaml.load(config_fh)

    # just name with correct value, this should be fine
    config_content["entry_fields"] = [{"name": "just_name", "required": False}]
    with open(setup_env / "changelog.d" / "config.yaml", "w+") as config_fh:
        yaml.dump(config_content, config_fh)

    caplog.clear()
    entry = runner.invoke(commands.entry, input="1\n\n")
    assert entry.exit_code == 0

    importlib.reload(commands)
    # make sure that missing verbose_name doesn't cause a problem
    entry = runner.invoke(
        commands.entry,
        ["--help"],
    )
    assert entry.exit_code == 0
    # also the `--just-name` option won't have any help
    assert (
        entry.stdout
        == """Usage: entry [OPTIONS]

  Create a new changelog entry.

Options:
  -v, --verbose     Increase verbosity.
  --just-name TEXT
  --type TEXT       Message type (as number or string).
  --help            Show this message and exit.
"""
    )

    # name contains space, not good
    config_content["entry_fields"] = [{"name": "just name", "required": False}]
    with open(setup_env / "changelog.d" / "config.yaml", "w+") as config_fh:
        yaml.dump(config_content, config_fh)

    caplog.clear()
    entry = runner.invoke(commands.entry, input="1\n\n")
    assert entry.exit_code == 1
    assert (
        "The 'name' argument of an 'entry_fields' element cannot contain spaces."
        in caplog.messages
    )

    # no name at all, also bad
    config_content["entry_fields"] = [{"verbose_name": "just_name", "required": False}]
    with open(setup_env / "changelog.d" / "config.yaml", "w+") as config_fh:
        yaml.dump(config_content, config_fh)

    caplog.clear()
    entry = runner.invoke(commands.entry, input="1\n\n")
    assert entry.exit_code == 1
    assert "Each 'entry_fields' element needs to have 'name'." in caplog.messages


def test_user_data(monkeypatch, fake_process):
    namespace = SimpleNamespace()
    config = Config()
    config._data = {**DEFAULT_CONFIG}
    config._path = FakePath("/test")

    fake_process.register(
        ["git", "config", "--list"],
        stdout=("user.name=Some User\n" "user.email=user@example.com\n"),
    )
    fake_process.register(["git", "add", fake_process.any()])
    fake_process.keep_last_process(True)

    monkeypatch.setattr(getpass, "getuser", lambda: "test-user")
    monkeypatch.setattr(
        YAML, "dump", functools.partial(fake_yaml_dump, namespace=namespace)
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "git_email": "user@example.com",
        "git_user": "Some User",
        "issue_id": ["1"],
        "message": "1",
        "os_user": "test-user",
        "type": "feature",
    }

    config._data["user_data"] = ["os_user"]
    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "issue_id": ["1"],
        "message": "1",
        "os_user": "test-user",
        "type": "feature",
    }

    config._data["user_data"] = [
        "os_user:overridden_username",
        "git_user:overridden_git_user",
    ]
    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "issue_id": ["1"],
        "message": "1",
        "type": "feature",
        "overridden_username": "test-user",
        "overridden_git_user": "Some User",
    }

    config._data["user_data"] = None
    changelogd.entry(config, {})
    assert namespace.data.pop("timestamp")
    assert namespace.data == {
        "issue_id": ["1"],
        "message": "1",
        "type": "feature",
    }

    config._data["user_data"] = ["not_exist"]

    with pytest.raises(SystemExit) as exc:
        changelogd.entry(config, {})
    assert str(exc.value) == (
        "The 'not_exist' variable is not supported in 'user_data'. "
        "Available choices are: 'os_user, git_user, git_email'."
    )
