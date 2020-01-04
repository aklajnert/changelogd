import os
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


def test_non_interactive_data(setup_env):
    runner = CliRunner()
    runner.invoke(commands.init)

    entry = runner.invoke(
        commands.entry,
        ["--type", "1", "--message", "test message"],
        input=os.linesep.join(["", ""]),
    )
    assert entry.exit_code == 0
