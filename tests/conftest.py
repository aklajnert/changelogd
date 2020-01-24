import datetime
import getpass
import os
import typing
from pathlib import Path

import pytest
from click.testing import CliRunner

from changelogd import config

old_invoke = CliRunner.invoke


def invoke(*args, **kwargs):
    result = old_invoke(*args, **kwargs)
    config.Config.settings = {}
    return result


CliRunner.invoke = invoke


@pytest.fixture
def setup_env(fake_process, monkeypatch, tmpdir, fake_date):
    fake_process.allow_unregistered(True)
    fake_process.keep_last_process(True)
    fake_process.register_subprocess(
        ["git", "config", "--list"],
        stdout=("user.name=Some User\n" "user.email=user@example.com\n"),
    )
    monkeypatch.setattr(getpass, "getuser", lambda: "test-user")
    monkeypatch.setattr(config, "DEFAULT_PATH", Path(tmpdir) / "changelog.d")
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(datetime, "date", fake_date)
    monkeypatch.setattr(os.path, "getmtime", lambda _: fake_date.EPOCH_02_02_2020)
    fake_date.set_date(datetime.date(2020, 2, 2))
    yield tmpdir


class FakeDate(datetime.date):
    EPOCH_02_02_2020 = 1580608922
    EPOCH_03_02_2020 = 1580695322
    _date = None

    @classmethod
    def today(cls) -> datetime.date:
        if not cls._date:
            return super().today()
        return cls._date

    @classmethod
    def set_date(cls, date: datetime.date) -> None:
        cls._date = date


class FakeNow:
    def __init__(self, timestamp):
        self._timestamp = timestamp

    def timestamp(self):
        return self._timestamp


class FakeDateTime(datetime.datetime):
    timestamp = 0

    @classmethod
    def now(cls, tz=None):
        cls.timestamp += 1
        return FakeNow(cls.timestamp)


@pytest.fixture()
def fake_date() -> typing.Type[FakeDate]:
    return FakeDate
