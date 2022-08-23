import logging
import os

from changelogd.utils import add_to_git
from changelogd.utils import get_git_data


def test_get_git_data(fake_process):
    fake_process.register_subprocess(
        ["git", "config", "--list"],
        stdout=(
            "core.symlinks=false\n"
            "core.autocrlf=true\n"
            "core.fscache=true\n"
            "rebase.autosquash=true\n"
            "diff.astextplain.textconv=astextplain\n"
            "user.name=Some User\n"
            "user.email=user@example.com\n"
            "core.bare=false\n"
            "core.logallrefupdates=true\n"
            "core.symlinks=false\n"
            "core.ignorecase=true\n"
            "branch.master.remote=origin\n"
            "branch.master.merge=refs/heads/master\n"
        ),
    )

    git_data = get_git_data()
    assert git_data == ("Some User", "user@example.com")


def test_get_git_data_failed(fake_process):
    fake_process.register_subprocess(["git", "config", "--list"], returncode=1)
    assert get_git_data() is None


def test_add_to_git(fake_process, caplog):
    caplog.set_level(logging.INFO)
    fake_process.register_subprocess(["git", "add", "/test"])
    fake_process.register_subprocess(
        ["git", "add", "/other-test"], returncode=1, stderr="error message"
    )

    add_to_git("/test")
    assert "Added to git: /test" in caplog.messages

    caplog.clear()
    add_to_git("/other-test")
    assert f"Failed to add to git: error message" in caplog.messages
