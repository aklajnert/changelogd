#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `changelogd` package."""

import datetime
import glob
import os
import sys
from pathlib import Path

import click
from click.testing import CliRunner
from ruamel.yaml import YAML

from changelogd import cli
from changelogd import commands
from changelogd import config
from tests.conftest import FakeDateTime

if sys.version_info >= (3, 8):
    from importlib import metadata as imp_metadata

    _HAVE_IMPORTLIB_METADATA = True
else:
    _HAVE_IMPORTLIB_METADATA = False


yaml = YAML()

BASE = """# Changelog  

"""
INITIAL_RELEASE = """
## initial-release (2020-02-02)  

This is the initial release.  

### Features  
* [#101](http://repo/issues/101): Another test feature ([@test-user](mailto:user@example.com))  
* [#100](http://repo/issues/100): Test feature ([@test-user](mailto:user@example.com))  

### Bug fixes  
* [#102](http://repo/issues/102): Bug fixes ([@test-user](mailto:user@example.com))  

### Documentation changes  
* Slight docs update ([@test-user](mailto:user@example.com))  
"""

PARTIAL_RELEASE_HEADER = """
## unreleased (2020-02-03)  
"""
SECOND_RELEASE_HEADER = """
## second-release (2020-02-03)  
"""
SECOND_RELEASE = """
### Features  
* [#202](http://repo/issues/202), [#203](http://repo/issues/203), [#204](http://repo/issues/204): Something new ([@test-user](mailto:user@example.com))  
* Great feature ([@test-user](mailto:user@example.com))  
* [#201](http://repo/issues/201): Super cool feature ([@test-user](mailto:user@example.com))  

### Deprecations  
* [#200](http://repo/issues/200): Deprecated test feature ([@test-user](mailto:user@example.com))  

### Other changes  
* Refactor ([@test-user](mailto:user@example.com))  

"""
SECOND_RELEASE_UPDATED = """
### Features  
* [#205](http://repo/issues/205): last-minute-change ([@test-user](mailto:user@example.com))  
* [#202](http://repo/issues/202), [#203](http://repo/issues/203), [#204](http://repo/issues/204): Something new ([@test-user](mailto:user@example.com))  
* Great feature ([@test-user](mailto:user@example.com))  
* [#201](http://repo/issues/201): Super cool feature ([@test-user](mailto:user@example.com))  

### Bug fixes  
* [#206](http://repo/issues/206): last-minute-change-2 ([@test-user](mailto:user@example.com))  

### Deprecations  
* [#200](http://repo/issues/200): Deprecated test feature ([@test-user](mailto:user@example.com))  

### Other changes  
* Refactor ([@test-user](mailto:user@example.com))  

"""


def _click_version():
    """Get the (major, minor) version of `click`."""
    if _HAVE_IMPORTLIB_METADATA:
        # If this fails, we have bigger problems...
        version_str = imp_metadata.version("click")
    else:
        version_str = getattr(click, "__version__", "0.0")

    try:
        parts_int = [int(part) for part in version_str.split(".")[:2]]
    except ValueError:
        parts_int = (0, 0)

    try:
        return parts_int[0], parts_int[1]
    except IndexError:
        return 0, 0


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    assert result.exit_code == (2 if _click_version() >= (8, 2) else 0)
    assert "Changelogs without conflicts." in result.output
    help_result = runner.invoke(cli.cli, ["--help"])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output


def test_full_flow(setup_env, monkeypatch, caplog, fake_date):
    """
    This function tests full functionality from fresh start through few releases.
    """
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    runner = CliRunner()

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0
    assert sorted(_list_directory(setup_env)) == sorted(
        [
            "changelog.d/README.md",
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
            "changelog.d/README.md",
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
    _create_entry(runner, "1", "202,203,204", "Something new")
    assert _count_entry_files(setup_env) == 5

    fake_date.set_date(datetime.date(2020, 2, 3))
    monkeypatch.setattr(os.path, "getmtime", lambda _: fake_date.EPOCH_03_02_2020)
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
    directory_list = sorted(
        [
            "changelog.d/README.md",
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
    assert sorted(_list_directory(setup_env)) == directory_list
    assert _count_entry_files(setup_env) == 0

    # two last-minute changes were added
    entry = runner.invoke(
        commands.entry,
        ["--release", "second-release"],
        input=os.linesep.join(["1", "205", "last-minute-change"]),
    )
    assert entry.exit_code == 0
    entry = runner.invoke(
        commands.entry,
        ["--release", "second-release"],
        input=os.linesep.join(["2", "206", "last-minute-change-2"]),
    )
    assert entry.exit_code == 0

    assert sorted(_list_directory(setup_env)) == directory_list

    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0

    changelog = _read_changelog(setup_env)
    assert (
        changelog
        == BASE + SECOND_RELEASE_HEADER + SECOND_RELEASE_UPDATED + INITIAL_RELEASE
    )
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

    # running release with --empty should also pass and generate a new release
    release = runner.invoke(commands.release, ["third-release", "--empty"], "\n")
    assert release.exit_code == 0
    new_changelog = _read_changelog(setup_env)
    assert changelog != new_changelog


def test_partial_releases(setup_env, caplog, fake_date):
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
    assert len(caplog.messages) == 1

    # even the next day shouldn't cause --check to fail
    caplog.clear()
    fake_date.set_date(datetime.date(2020, 2, 3))
    partial = runner.invoke(commands.partial, ["--check"])
    assert partial.exit_code == 0
    assert len(caplog.messages) == 1

    # but running partial without --check should update the timestamp
    caplog.clear()
    changelog_before = _read_changelog(setup_env)
    partial = runner.invoke(commands.partial)
    assert partial.exit_code == 0
    assert len(caplog.messages) == 1
    assert changelog_before != _read_changelog(setup_env)


def test_empty_release(setup_env, caplog):
    """
    This is also a regression. The program was crashing when there was
    no releases and no entries with --empty argument.
    """
    HEADER = "# Changelog  \n\n\n"
    CHANGELOG_0_1_0 = "## 0.1.0 (2020-02-02)  \n\nInitial release  \n"
    CHANGELOG_0_1_1 = (
        "## 0.1.1 (2020-02-02)  \n\nPatch release  \n\n"
        "### Features  \n"
        "* Sample entry ([@test-user](mailto:user@example.com))  \n\n\n"
    )
    CHANGELOG_0_1_2 = "## 0.1.2 (2020-02-02)  \n\nMaintenance release  \n\n\n"

    runner = CliRunner()

    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    release = runner.invoke(commands.release, ["0.1.0", "--empty"], "Initial release\n")
    assert release.exit_code == 0

    changelog = _read_changelog(setup_env)
    assert changelog == HEADER + CHANGELOG_0_1_0

    _create_entry(runner, "1", "", "Sample entry")
    release = runner.invoke(commands.release, ["0.1.1"], "Patch release\n")
    assert release.exit_code == 0
    assert _read_changelog(setup_env) == HEADER + CHANGELOG_0_1_1 + CHANGELOG_0_1_0

    caplog.clear()
    release = runner.invoke(
        commands.release, ["0.1.2", "--empty"], "Maintenance release\n"
    )
    assert release.exit_code == 0
    assert (
        _read_changelog(setup_env)
        == HEADER + CHANGELOG_0_1_2 + CHANGELOG_0_1_1 + CHANGELOG_0_1_0
    )


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
        f"The configuration directory does not exist: {tmpdir / 'changelog.d'}.\n"
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


def test_init_rst(setup_env, monkeypatch, caplog, fake_date):
    runner = CliRunner()

    init = runner.invoke(commands.init, ["--rst"])
    assert init.exit_code == 0
    assert sorted(_list_directory(setup_env)) == sorted(
        [
            "changelog.d/README.md",
            "changelog.d/config.yaml",
            "changelog.d/releases/.gitkeep",
            "changelog.d/templates/entry.rst",
            "changelog.d/templates/main.rst",
            "changelog.d/templates/release.rst",
        ]
    )

    with Path(setup_env / "changelog.d" / "config.yaml").open() as config_fh:
        output_config = yaml.load(config_fh)

    assert output_config["output_file"] == "../changelog.rst"


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


def test_release_same_version(setup_env, monkeypatch, caplog, fake_date):
    """
    This function tests full functionality from fresh start through few releases.
    """
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    runner = CliRunner()

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    _create_entry(runner, "1", "100", "Test feature")

    # now release first version
    release = runner.invoke(commands.release, ["1.0"], "This is the initial release.")
    assert release.exit_code == 0

    # try second release with already existing version
    _create_entry(runner, "2", "102", "Bug fixes")
    release = runner.invoke(commands.release, ["1.0"], "This is the second release.")
    assert release.exit_code == 1
    assert "The release '1.0' already exists." in release.stdout

    # try second release with new version
    _create_entry(runner, "2", "102", "Bug fixes")
    release = runner.invoke(commands.release, ["1.1"], "This is the second release.")
    assert release.exit_code == 0

    directory_list = sorted(
        [
            "changelog.d/README.md",
            "changelog.d/config.yaml",
            "changelog.d/releases/.gitkeep",
            "changelog.d/releases/0.1.0.yaml",
            "changelog.d/releases/1.1.1.yaml",
            "changelog.d/templates/entry.md",
            "changelog.d/templates/main.md",
            "changelog.d/templates/release.md",
            "changelog.md",
        ]
    )
    assert sorted(_list_directory(setup_env)) == directory_list


def test_hotfix_release_between_versions(setup_env, monkeypatch, fake_date):
    """
    Test inserting a hotfix release between two existing releases.
    For example: after releasing 1.10 and 1.11, insert 1.10.1 between them.
    """
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    runner = CliRunner()

    HEADER = "# Changelog  \n\n\n"
    CHANGELOG_1_10 = (
        "## 1.10 (2020-02-02)  \n\nFirst release  \n\n"
        "### Features  \n"
        "* [#100](http://repo/issues/100): Feature for 1.10 "
        "([@test-user](mailto:user@example.com))  \n"
    )
    CHANGELOG_1_11 = (
        "## 1.11 (2020-02-02)  \n\nSecond release  \n\n"
        "### Features  \n"
        "* [#200](http://repo/issues/200): Feature for 1.11 "
        "([@test-user](mailto:user@example.com))  \n\n\n"
    )
    CHANGELOG_1_10_1 = (
        "## 1.10.1 (2020-02-02)  \n\nHotfix release  \n\n"
        "### Bug fixes  \n"
        "* [#150](http://repo/issues/150): Hotfix for 1.10 "
        "([@test-user](mailto:user@example.com))  \n\n\n"
    )

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    # create and release 1.10
    _create_entry(runner, "1", "100", "Feature for 1.10")
    release = runner.invoke(commands.release, ["1.10"], "First release\n")
    assert release.exit_code == 0

    # create and release 1.11
    _create_entry(runner, "1", "200", "Feature for 1.11")
    release = runner.invoke(commands.release, ["1.11"], "Second release\n")
    assert release.exit_code == 0

    # verify the changelog has 1.11 before 1.10
    changelog = _read_changelog(setup_env)
    assert changelog == HEADER + CHANGELOG_1_11 + CHANGELOG_1_10

    # verify the release files before hotfix
    directory_before = _list_directory(setup_env)
    assert "changelog.d/releases/0.1.10.yaml" in directory_before
    assert "changelog.d/releases/1.1.11.yaml" in directory_before

    # now insert a hotfix 1.10.1 between 1.10 and 1.11
    _create_entry(runner, "2", "150", "Hotfix for 1.10")
    release = runner.invoke(commands.release, ["1.10.1"], "Hotfix release\n")
    assert release.exit_code == 0

    # verify the changelog now has correct ordering: 1.11 > 1.10.1 > 1.10
    changelog = _read_changelog(setup_env)
    assert changelog == HEADER + CHANGELOG_1_11 + CHANGELOG_1_10_1 + CHANGELOG_1_10

    # verify the release files were renumbered correctly
    directory_after = _list_directory(setup_env)
    assert "changelog.d/releases/0.1.10.yaml" in directory_after
    assert "changelog.d/releases/1.1.10.1.yaml" in directory_after
    assert "changelog.d/releases/2.1.11.yaml" in directory_after
    # Ensure the old 1.1.11.yaml no longer exists (it was renumbered to 2.1.11.yaml)
    assert "changelog.d/releases/1.1.11.yaml" not in directory_after


def test_hotfix_release_at_beginning(setup_env, monkeypatch, fake_date):
    """
    Test inserting a version that should go before all existing releases.
    """
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    runner = CliRunner()

    HEADER = "# Changelog  \n\n\n"

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    # create and release 2.0
    _create_entry(runner, "1", "100", "Feature for 2.0")
    release = runner.invoke(commands.release, ["2.0"], "Second major\n")
    assert release.exit_code == 0

    # create and release 3.0
    _create_entry(runner, "1", "200", "Feature for 3.0")
    release = runner.invoke(commands.release, ["3.0"], "Third major\n")
    assert release.exit_code == 0

    # verify directory before inserting earlier version
    directory_before = _list_directory(setup_env)
    assert "changelog.d/releases/0.2.0.yaml" in directory_before
    assert "changelog.d/releases/1.3.0.yaml" in directory_before

    # now insert 1.0 which should go before everything
    _create_entry(runner, "1", "50", "Feature for 1.0")
    release = runner.invoke(commands.release, ["1.0"], "First major\n")
    assert release.exit_code == 0

    # verify directory: 1.0 should be id 0, 2.0 should be id 1, 3.0 should be id 2
    directory_after = _list_directory(setup_env)
    assert "changelog.d/releases/0.1.0.yaml" in directory_after
    assert "changelog.d/releases/1.2.0.yaml" in directory_after
    assert "changelog.d/releases/2.3.0.yaml" in directory_after
    # Ensure old files are gone (renumbered)
    assert "changelog.d/releases/0.2.0.yaml" not in directory_after
    assert "changelog.d/releases/1.3.0.yaml" not in directory_after

    # verify changelog ordering: 3.0 > 2.0 > 1.0
    changelog = _read_changelog(setup_env)
    pos_3_0 = changelog.index("## 3.0")
    pos_2_0 = changelog.index("## 2.0")
    pos_1_0 = changelog.index("## 1.0")
    assert pos_3_0 < pos_2_0 < pos_1_0


def test_multiple_hotfix_insertions(setup_env, monkeypatch, fake_date):
    """
    Test multiple hotfix insertions to verify repeated renumbering works.
    """
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    runner = CliRunner()

    # start with init
    init = runner.invoke(commands.init)
    assert init.exit_code == 0

    # create releases 1.0, 2.0, 3.0
    for version in ["1.0", "2.0", "3.0"]:
        _create_entry(runner, "1", "", f"Feature for {version}")
        release = runner.invoke(commands.release, [version], f"Release {version}\n")
        assert release.exit_code == 0

    # insert 1.1 between 1.0 and 2.0
    _create_entry(runner, "2", "", "Bugfix for 1.1")
    release = runner.invoke(commands.release, ["1.1"], "Hotfix 1.1\n")
    assert release.exit_code == 0

    # verify files before second insertion
    directory_before_second = _list_directory(setup_env)
    assert "changelog.d/releases/0.1.0.yaml" in directory_before_second
    assert "changelog.d/releases/1.1.1.yaml" in directory_before_second
    assert "changelog.d/releases/2.2.0.yaml" in directory_before_second
    assert "changelog.d/releases/3.3.0.yaml" in directory_before_second

    # insert 1.0.1 between 1.0 and 1.1
    _create_entry(runner, "2", "", "Bugfix for 1.0.1")
    release = runner.invoke(commands.release, ["1.0.1"], "Hotfix 1.0.1\n")
    assert release.exit_code == 0

    # verify all files exist with correct numbering after second insertion
    directory_after_second = _list_directory(setup_env)
    assert "changelog.d/releases/0.1.0.yaml" in directory_after_second
    assert "changelog.d/releases/1.1.0.1.yaml" in directory_after_second
    assert "changelog.d/releases/2.1.1.yaml" in directory_after_second
    assert "changelog.d/releases/3.2.0.yaml" in directory_after_second
    assert "changelog.d/releases/4.3.0.yaml" in directory_after_second
    # Ensure old files are gone (renumbered)
    assert "changelog.d/releases/1.1.1.yaml" not in directory_after_second
    assert "changelog.d/releases/2.2.0.yaml" not in directory_after_second
    assert "changelog.d/releases/3.3.0.yaml" not in directory_after_second

    # verify changelog ordering: 3.0 > 2.0 > 1.1 > 1.0.1 > 1.0
    changelog = _read_changelog(setup_env)
    pos_3_0 = changelog.index("## 3.0")
    pos_2_0 = changelog.index("## 2.0")
    pos_1_1 = changelog.index("## 1.1")
    pos_1_0_1 = changelog.index("## 1.0.1")
    pos_1_0 = changelog.index("## 1.0 ")  # space to avoid matching 1.0.1
    assert pos_3_0 < pos_2_0 < pos_1_1 < pos_1_0_1 < pos_1_0
