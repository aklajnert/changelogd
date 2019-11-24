import logging
import typing

import click

from .config import Config


def command_decorator(func: typing.Callable) -> click.core.Command:
    pass_state = click.make_pass_decorator(Config, ensure=True)
    verbose = click.option(
        *("-v", "--verbose"),
        count=True,
        help="Increase verbosity.",
        callback=Config.set_verbosity  # type: ignore
    )
    return click.command()(verbose(pass_state(click.pass_context(func))))


@command_decorator
def init(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Initialize changelogd config."""
    logging.warning("init")
    logging.info("test")


@command_decorator
def draft(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Generate draft changelog."""
    print("draft")


@command_decorator
def release(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Generate changelog, clear entries and make a new release."""
    print("release")


@command_decorator
def entry(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Create a new changelog entry."""
    print("entry")


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, release, entry)

    for command in commands:
        cli.add_command(command)
