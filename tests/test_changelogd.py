#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `changelogd` package."""
import datetime
import glob
import os
from pathlib import Path

from click.testing import CliRunner

from changelogd import cli
from changelogd import commands
from changelogd import config

DRAFT = """# Changelog  

## beta-version (2020-02-02)  

This is a test release.  

### Features  
* [#101](http://repo/issues/101): Another test feature  
* [#100](http://repo/issues/100): Test feature  

### Bug fixes  
* [#102](http://repo/issues/102): Bug fixes  

### Documentation changes  
* Slight docs update  
  
"""


class FakeDate(datetime.date):
    _date = None

    @classmethod
    def today(cls) -> datetime.date:
        if not cls._date:
            return super().today()
        return cls._date

    @classmethod
    def set_date(cls, date: datetime.date) -> None:
        cls._date = date


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    assert result.exit_code == 0
    assert "Changelogs without conflicts." in result.output
    help_result = runner.invoke(cli.cli, ["--help"])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output


def test_full_flow(tmpdir, monkeypatch):
    monkeypatch.setattr(config, "DEFAULT_PATH", Path(tmpdir) / "changelog.d")
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(datetime, "date", FakeDate)
    FakeDate.set_date(datetime.date(2020, 2, 2))

    runner = CliRunner()

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0
    assert sorted(_list_directory(tmpdir)) == sorted(
        [
            "changelog.d/config.yaml",
            "changelog.d/releases/.gitkeep",
            "changelog.d/templates/entry.md",
            "changelog.d/templates/main.md",
            "changelog.d/templates/release.md",
        ]
    )

    # add some entries
    _create_entry(runner, "1", "100", "Test feature")
    _create_entry(runner, "1", "101", "Another test feature")
    _create_entry(runner, "2", "102", "Bug fixes")
    _create_entry(runner, "3", "", "Slight docs update")
    assert (
        len(glob.glob((Path(tmpdir) / "changelog.d" / "*entry.yaml").as_posix())) == 4
    )

    # try draft release
    draft = runner.invoke(commands.draft, ["beta-version"], "This is a test release.")
    assert draft.exit_code == 0
    output = draft.stdout[len("Release description (hit ENTER to omit): ") :]
    assert output == DRAFT


def _list_directory(directory):
    output = []
    for root, dirs, files in os.walk(directory):
        for file_ in files:
            output.append((Path(root) / file_).relative_to(directory).as_posix())

    return output


def _create_entry(runner, type, issue_id, message):
    entry = runner.invoke(
        commands.entry, input=os.linesep.join([type, issue_id, message])
    )
    assert entry.exit_code == 0
