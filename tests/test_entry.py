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


def test_incorrect_input_entry(fs):
    runner = CliRunner()

    entry = runner.invoke(commands.entry,)
    assert entry.exit_code == 1
