import glob
import importlib
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from changelogd import commands
from changelogd import config


@pytest.fixture()
def prepare_config(fs):
    config_dir = Path("changelog.d")
    fs.create_dir(config_dir)
    with (config_dir / "config.yaml").open("w+") as config_fh:
        yaml.dump(config.DEFAULT_CONFIG, config_fh)


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

    entry = runner.invoke(commands.entry, ["--help"],)
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

    assert entry_content == {
        "git_email": "user@example.com",
        "git_user": "Some User",
        "issue_id": "100",
        "message": "test message",
        "os_user": "test-user",
        "type": "feature",
    }
