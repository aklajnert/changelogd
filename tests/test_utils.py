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
