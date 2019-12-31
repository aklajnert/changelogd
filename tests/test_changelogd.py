#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `changelogd` package."""
import datetime
import getpass
import glob
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from changelogd import cli
from changelogd import commands
from changelogd import config

EPOCH_02_02_2020 = 1580608922
EPOCH_03_02_2020 = 1580695322

BASE = """# Changelog  

"""
INITIAL_RELEASE = """
## initial-release (2020-02-02)  

This is the initial release.  

### Features  
* [#100](http://repo/issues/100): Test feature ([@test-user](user@example.com))  
* [#101](http://repo/issues/101): Another test feature ([@test-user](user@example.com))  

### Bug fixes  
* [#102](http://repo/issues/102): Bug fixes ([@test-user](user@example.com))  

### Documentation changes  
* Slight docs update ([@test-user](user@example.com))  
"""

PARTIAL_RELEASE_HEADER = """
## unreleased (2020-02-03)  
"""
SECOND_RELEASE_HEADER = """
## second-release (2020-02-03)  
"""
SECOND_RELEASE = """
### Features  
* [#202](http://repo/issues/202): Something new ([@test-user](user@example.com))  
* Great feature ([@test-user](user@example.com))  
* [#201](http://repo/issues/201): Super cool feature ([@test-user](user@example.com))  

### Deprecations  
* [#200](http://repo/issues/200): Deprecated test feature ([@test-user](user@example.com))  

### Other changes  
* Refactor ([@test-user](user@example.com))  

"""


@pytest.fixture
def setup_env(fake_process, monkeypatch, tmpdir):
    fake_process.keep_last_process(True)
    fake_process.register_subprocess(
        ["git", "config", "--list"],
        stdout=("user.name=Some User\n" "user.email=user@example.com\n"),
    )
    monkeypatch.setattr(getpass, "getuser", lambda: "test-user")
    monkeypatch.setattr(config, "DEFAULT_PATH", Path(tmpdir) / "changelog.d")
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(datetime, "date", FakeDate)
    monkeypatch.setattr(os.path, "getmtime", lambda _: EPOCH_02_02_2020)
    FakeDate.set_date(datetime.date(2020, 2, 2))
    yield tmpdir


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


def test_full_flow(setup_env, monkeypatch, caplog):
    """
    This function tests full functionality from fresh start through few releases.
    """

    runner = CliRunner()

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0
    assert sorted(_list_directory(setup_env)) == sorted(
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
    assert _count_entry_files(setup_env) == 4

    # try draft release
    draft = runner.invoke(
        commands.draft, ["initial-release"], "This is the initial release."
    )
    assert draft.exit_code == 0
    output = draft.stdout[len("Release description (hit ENTER to omit): ") :]
    assert output == BASE + INITIAL_RELEASE + "\n"

    # now release first version
    release = runner.invoke(
        commands.release, ["initial-release"], "This is the initial release."
    )
    assert release.exit_code == 0
    assert sorted(_list_directory(setup_env)) == sorted(
        [
            "changelog.d/config.yaml",
            "changelog.d/releases/.gitkeep",
            "changelog.d/releases/0.initial-release.yaml",
            "changelog.d/templates/entry.md",
            "changelog.d/templates/main.md",
            "changelog.d/templates/release.md",
            "changelog.md",
        ]
    )
    changelog = _read_changelog(setup_env)

    assert changelog == BASE + INITIAL_RELEASE

    # create some other entries
    _create_entry(runner, "4", "200", "Deprecated test feature")
    _create_entry(runner, "1", "201", "Super cool feature")
    _create_entry(runner, "5", "", "Refactor")
    _create_entry(runner, "1", "", "Great feature")
    _create_entry(runner, "1", "202", "Something new")
    assert _count_entry_files(setup_env) == 5

    FakeDate.set_date(datetime.date(2020, 2, 3))
    monkeypatch.setattr(os.path, "getmtime", lambda _: EPOCH_03_02_2020)
    # try a partial release
    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0

    assert _count_entry_files(setup_env) == 5

    changelog = _read_changelog(setup_env)
    assert changelog == BASE + PARTIAL_RELEASE_HEADER + SECOND_RELEASE + INITIAL_RELEASE

    # another partial release shall generate exactly the same output
    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0

    assert changelog == _read_changelog(setup_env)

    # release a new version
    release = runner.invoke(commands.release, ["second-release"], "\n")
    assert release.exit_code == 0
    assert sorted(_list_directory(setup_env)) == sorted(
        [
            "changelog.d/config.yaml",
            "changelog.d/releases/.gitkeep",
            "changelog.d/releases/0.initial-release.yaml",
            "changelog.d/releases/1.second-release.yaml",
            "changelog.d/templates/entry.md",
            "changelog.d/templates/main.md",
            "changelog.d/templates/release.md",
            "changelog.md",
        ]
    )
    assert _count_entry_files(setup_env) == 0

    changelog = _read_changelog(setup_env)
    assert changelog == BASE + SECOND_RELEASE_HEADER + SECOND_RELEASE + INITIAL_RELEASE
    caplog.clear()

    # another attempt to release shall raise an error due to no entries
    release = runner.invoke(commands.release, ["third-release"], "\n")
    assert release.exit_code == 1
    assert "Cannot create new release without any entries." in caplog.messages
    caplog.clear()

    # same should happen for draft
    draft = runner.invoke(commands.draft, ["third-release"], "\n")
    assert draft.exit_code == 1
    assert "Cannot create new release without any entries." in caplog.messages
    caplog.clear()

    # but another attempt to partial release should be fine
    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0
    # however, changelog shouldn't be modified
    new_changelog = _read_changelog(setup_env)
    assert changelog == new_changelog

    # even with the --check argument
    partial = runner.invoke(commands.partial, ["--check"])
    assert partial.exit_code == 0


def test_partial_releases(setup_env, caplog):
    """Test more sophisticated scenarios with partial releases."""
    runner = CliRunner()

    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    _create_entry(runner, "1", "1", "First entry")
    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0

    _create_entry(runner, "1", "2", "Second entry")
    # now run partial with --check, which should fail
    caplog.clear()
    partial = runner.invoke(commands.partial, ["--check"])
    assert partial.exit_code == 1
    assert "Output file content is different than before." in caplog.messages

    # another partial should pass, since previous partial updated the changelog
    caplog.clear()
    partial = runner.invoke(commands.partial, ["--check"])
    assert partial.exit_code == 0
    assert not caplog.messages

    # even the next day shouldn't cause --check to fail
    FakeDate.set_date(datetime.date(2020, 2, 3))
    partial = runner.invoke(commands.partial, ["--check"])
    assert partial.exit_code == 0
    assert not caplog.messages


def test_init(tmpdir, monkeypatch, caplog):
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(config, "DEFAULT_PATH", Path(tmpdir) / "changelog.d")
    with open(tmpdir / "setup.cfg", "w+") as setup_file:
        setup_file.write("[tool:pytest]\ncollect_ignore = ['setup.py']")

    runner = CliRunner()

    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    config_yaml = tmpdir / "changelog.d" / "config.yaml"
    assert f"Created main configuration file: {config_yaml}" in caplog.messages
    assert (
        f"Copied templates to {tmpdir / 'changelog.d' / 'templates'}" in caplog.messages
    )
    assert (
        f"The configuration path is not standard, please add a following snippet to "
        f"the '{tmpdir / 'setup.cfg'}' file:\n\n[tool:changelogd]\n"
        f"config={config_yaml}" not in caplog.messages
    )


def test_no_init(tmpdir, monkeypatch):
    """All commands, except `init` should crash if no configuration is found."""
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(config, "DEFAULT_PATH", Path(tmpdir) / "changelog.d")

    runner = CliRunner()

    error = (
        f"The configuration directory does not exist: {tmpdir/'changelog.d'}.\n"
        f"Run `changelogd init` to create it.\n"
    )

    def check_command(command):
        result = runner.invoke(*command)
        assert result.exit_code == 1
        assert result.stdout == error

    test_commands = (
        (commands.entry,),
        (commands.draft, ["version"]),
        (commands.release, ["version"]),
        (commands.partial,),
    )

    for command in test_commands:
        check_command(command)

    init = runner.invoke(commands.init)
    assert init.exit_code == 0


def _count_entry_files(tmpdir):
    return len(glob.glob((Path(tmpdir) / "changelog.d" / "*entry.yaml").as_posix()))


def _read_changelog(tmpdir):
    with open(tmpdir / "changelog.md") as changelog_fh:
        changelog = changelog_fh.read()
    return changelog


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
